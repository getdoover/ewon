#!/usr/bin/env python3
"""Re-stamp Ewon frame records that were logged in the wrong timezone.

Background
----------
The Ewon DataMailbox processor used to interpret every DataMailbox ``date`` as
the Ewon's local clock and re-label it with the configured "Ewon Clock
Timezone" (Australia/Adelaide for the Ennovo sites). A replacement Ewon at
Anglesea has "Record data in UTC" enabled, so its dates were already UTC and
every frame landed ``utcoffset(clock_tz)`` early - 9h30m before Adelaide
daylight saving, 10h30m after.

This script walks the ``tag_values`` channel for a window, finds the frame
record-log messages, re-creates each one at the time the Ewon actually
reported, and only then deletes the original. It never touches the channel
aggregate, the live "echo" messages the processor also wrote at wall-clock
time, or anything outside the window.

Run it ONLY after the fixed processor is deployed and ``--before`` is set to
the deploy time, otherwise correctly-stamped new frames will be shifted too.

Usage
-----
    # dry run (default) - prints what would change, writes nothing
    uv run python data_analysis/fix_anglesea_timestamps.py \
        --before 2026-09-15T00:00:00Z

    # do it
    uv run python data_analysis/fix_anglesea_timestamps.py \
        --before 2026-09-15T00:00:00Z --live

Auth comes from the Doover CLI profile (``doover login``), default profile
"default" - the prod Doover 2.0 profile pointing at data.doover.com.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from pydoover.api import DataClient

# Newer pydoover exposes batch message mutations (50 per request). The
# version pinned in this repo's uv.lock predates them, so fall back to one
# request per message - ~550 frames is only a couple of minutes either way.
try:
    from pydoover.models.data.batch import BatchMutationItem
except ImportError:  # pragma: no cover - depends on pinned pydoover
    BatchMutationItem = None
BATCH_SIZE = 50

log = logging.getLogger("fix_anglesea_timestamps")

TAG_CHANNEL = "tag_values"

DEFAULT_AGENT = 127202016203148037  # anglesea-flare (Ennovo)
DEFAULT_APP_KEY = "ewon_processor_1"
DEFAULT_CLOCK_TZ = "Australia/Adelaide"
# First frame the replacement unit produced, as it currently sits in Doover
# (real time 2026-09-08 12:20:56Z, shifted back 9h30m). Nothing before it needs
# touching: the old unit's last frame was 2026-08-06.
DEFAULT_AFTER = "2026-09-08T02:00:00Z"


def parse_utc(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def corrected_timestamp(stored: datetime, clock_tz: ZoneInfo) -> datetime:
    """Undo ``datetime.fromisoformat(date).replace(tzinfo=clock_tz)``.

    The processor took a UTC wall-clock string and declared it to be in
    ``clock_tz``. Converting the stored instant back into ``clock_tz`` recovers
    that wall-clock reading, which was the true UTC time all along. Doing it
    this way (rather than adding a fixed 9h30m) stays correct across the
    daylight-saving boundary.
    """
    wall = stored.astimezone(clock_tz).replace(tzinfo=None)
    return wall.replace(tzinfo=timezone.utc)


def is_frame_message(msg, app_key: str) -> bool:
    """Frame record logs carry an explicit whole-second timestamp.

    The wall-clock "echo" messages pydoover wrote at the end of each
    invocation have millisecond precision, because the platform stamped them
    on arrival. Ewon samples are always on a whole second.
    """
    if msg.timestamp.microsecond != 0:
        return False
    data = msg.data or {}
    return isinstance(data.get(app_key), dict)


def iter_window(client, agent: int, channel: str, after: datetime, before: datetime):
    """Page through every message in (after, before), newest first.

    Done by hand rather than via ``client.iter_messages`` because the pinned
    pydoover's iterator mis-passes its arguments when both bounds are set.
    """
    cursor = before
    seen: set[int] = set()
    while True:
        page = client.list_messages(agent, channel, before=cursor, after=after, limit=100)
        page = [m for m in page if m.id not in seen]
        if not page:
            return
        for m in page:
            seen.add(m.id)
            yield m
        # Snowflake ids order by time, so the smallest id is the oldest message.
        cursor = min(m.id for m in page)


def chunked(items, size=BATCH_SIZE):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def has_batch_api(client) -> bool:
    return BatchMutationItem is not None and all(
        hasattr(client, n) for n in ("batch_create_messages", "batch_delete_messages")
    )


def create_messages(client, agent: int, batch: list[tuple[object, datetime]]):
    """Create one message per (original, new_timestamp). Yields (original, new_id | None, error)."""
    if has_batch_api(client):
        items = [
            BatchMutationItem(agent, TAG_CHANNEL, data=m.data, timestamp=ts)
            for m, ts in batch
        ]
        resp = client.batch_create_messages(items)
        for (m, _), r in zip(batch, resp.items):
            yield m, (r.message_id if r.success else None), (None if r.success else r.error)
        return
    for m, ts in batch:
        try:
            created = client.create_message(
                agent, TAG_CHANNEL, m.data, timestamp=int(ts.timestamp() * 1000)
            )
        except Exception as exc:  # noqa: BLE001 - report and carry on
            yield m, None, str(exc)
        else:
            yield m, created.id, None


def delete_messages(client, agent: int, batch: list):
    """Delete each message in ``batch``. Yields (original, error | None)."""
    if has_batch_api(client):
        items = [BatchMutationItem(agent, TAG_CHANNEL, message_id=m.id) for m in batch]
        resp = client.batch_delete_messages(items)
        for m, r in zip(batch, resp.items):
            yield m, (None if r.success else r.error)
        return
    for m in batch:
        try:
            client.delete_message(agent, TAG_CHANNEL, m.id)
        except Exception as exc:  # noqa: BLE001
            yield m, str(exc)
        else:
            yield m, None


def fmt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--agent", type=int, default=DEFAULT_AGENT)
    parser.add_argument("--app-key", default=DEFAULT_APP_KEY)
    parser.add_argument("--profile", default="default", help="Doover CLI profile")
    parser.add_argument(
        "--clock-tz",
        default=DEFAULT_CLOCK_TZ,
        help="The 'Ewon Clock Timezone' the processor was configured with",
    )
    parser.add_argument(
        "--after",
        default=DEFAULT_AFTER,
        help="Only touch messages after this UTC time (ISO-8601)",
    )
    parser.add_argument(
        "--before",
        required=True,
        help="Only touch messages before this UTC time (ISO-8601). "
        "Set this to when the fixed processor went live.",
    )
    parser.add_argument(
        "--keep-first-frame",
        action="store_true",
        help="Re-stamp the earliest frame too. By default it is deleted "
        "without replacement, because a freshly installed Ewon's first "
        "sample is the stale values it inherited (flow 0, temp ~10C).",
    )
    parser.add_argument(
        "--trial",
        type=int,
        metavar="N",
        help="Live mode only: stop after re-stamping the first N frames.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Actually write. Without this the script is a dry run.",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Where to record created/deleted message ids "
        "(default: next to this script, timestamped).",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    clock_tz = ZoneInfo(args.clock_tz)
    after = parse_utc(args.after)
    before = parse_utc(args.before)
    if before <= after:
        parser.error("--before must be later than --after")
    if before > datetime.now(tz=timezone.utc):
        parser.error("--before is in the future; set it to the deploy time")

    mode = "LIVE" if args.live else "DRY RUN"
    log.info(
        f"{mode}: agent={args.agent} app_key={args.app_key} "
        f"window=[{fmt(after)}Z, {fmt(before)}Z) clock_tz={args.clock_tz}"
    )

    client = DataClient(profile=args.profile)

    # ── collect ─────────────────────────────────────────────────────────────
    frames = []
    echoes = 0
    for msg in iter_window(client, args.agent, TAG_CHANNEL, after, before):
        if is_frame_message(msg, args.app_key):
            frames.append(msg)
        else:
            echoes += 1

    frames.sort(key=lambda m: m.timestamp)
    if not frames:
        log.info("No frame messages in window; nothing to do.")
        return 0

    dropped = None
    if not args.keep_first_frame:
        dropped = frames.pop(0)

    log.info(f"Found {len(frames)} frame messages to re-stamp, {echoes} wall-clock messages left alone")
    if dropped is not None:
        vals = dropped.data.get(args.app_key, {})
        log.info(
            f"First frame {fmt(dropped.timestamp)}Z will be deleted, not re-stamped: "
            + json.dumps({k: vals.get(k) for k in ("Gas_Flow", "Temperature", "Run_Hours")})
        )

    shifts = {corrected_timestamp(m.timestamp, clock_tz) - m.timestamp for m in frames}
    log.info("Shift(s) to apply: " + ", ".join(str(s) for s in sorted(shifts)))
    log.info(
        f"Earliest: {fmt(frames[0].timestamp)}Z -> {fmt(corrected_timestamp(frames[0].timestamp, clock_tz))}Z"
    )
    log.info(
        f"Latest:   {fmt(frames[-1].timestamp)}Z -> {fmt(corrected_timestamp(frames[-1].timestamp, clock_tz))}Z"
    )
    latest_new = corrected_timestamp(frames[-1].timestamp, clock_tz)
    if latest_new >= before:
        log.warning(
            f"Re-stamped frames will extend to {fmt(latest_new)}Z, past --before. "
            "Make sure the fixed processor really went live at --before, or these "
            "will overlap frames it has written since."
        )

    for m in frames[:3] + ([None] if len(frames) > 6 else []) + frames[-3:]:
        if m is None:
            log.info("   ...")
            continue
        vals = m.data.get(args.app_key, {})
        log.info(
            f"   {fmt(m.timestamp)}Z -> {fmt(corrected_timestamp(m.timestamp, clock_tz))}Z  "
            + json.dumps({k: vals.get(k) for k in ("Gas_Flow", "Temperature", "Run_Hours")})
        )

    if not args.live:
        log.info("Dry run complete. Re-run with --live to apply.")
        return 0

    # ── apply ───────────────────────────────────────────────────────────────
    if args.trial:
        frames = frames[: args.trial]
        log.info(f"TRIAL: limiting to first {len(frames)} frames; first frame is NOT dropped in trial mode")
        dropped = None

    log_file = args.log_file or Path(__file__).with_name(
        f"fix_anglesea_timestamps.{datetime.now(tz=timezone.utc):%Y%m%dT%H%M%SZ}.json"
    )
    journal = {"agent": args.agent, "channel": TAG_CHANNEL, "created": [], "deleted": [], "failed": []}

    def flush_journal():
        log_file.write_text(json.dumps(journal, indent=1, default=str))

    # Phase 1: create the corrected copies. If this dies half way we have
    # duplicates (recoverable from the journal), never missing data.
    log.info("Using " + ("batch" if has_batch_api(client) else "per-message") + " API")
    created_ok = []
    for batch in chunked(frames):
        pairs = [(m, corrected_timestamp(m.timestamp, clock_tz)) for m in batch]
        for original, new_id, error in create_messages(client, args.agent, pairs):
            if error is None:
                created_ok.append(original)
                journal["created"].append(
                    {
                        "new_id": new_id,
                        "from_id": original.id,
                        "ts": fmt(corrected_timestamp(original.timestamp, clock_tz)),
                    }
                )
            else:
                journal["failed"].append({"op": "create", "id": original.id, "error": error})
                log.error(f"create failed for {original.id} @ {fmt(original.timestamp)}Z: {error}")
        flush_journal()
        log.info(f"created {len(created_ok)}/{len(frames)}")

    if journal["failed"]:
        log.error(
            f"{len(journal['failed'])} creates failed; NOT deleting any originals. "
            f"See {log_file}. Fix and re-run with a narrower window, or delete the "
            "successfully created copies listed in the journal before retrying."
        )
        return 1

    # Phase 2: delete the originals (and the stale first frame).
    to_delete = created_ok + ([dropped] if dropped is not None else [])
    deleted = 0
    for batch in chunked(to_delete):
        for original, error in delete_messages(client, args.agent, batch):
            if error is None:
                deleted += 1
                journal["deleted"].append(original.id)
            else:
                journal["failed"].append({"op": "delete", "id": original.id, "error": error})
                log.error(f"delete failed for {original.id} @ {fmt(original.timestamp)}Z: {error}")
        flush_journal()
        log.info(f"deleted {deleted}/{len(to_delete)}")

    log.info(f"Done. Journal written to {log_file}")
    return 1 if journal["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
