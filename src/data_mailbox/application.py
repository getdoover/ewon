import asyncio
import logging
from datetime import UTC, datetime, timedelta

import aiohttp
from pydoover.rpc import RPCError

from ewon_common import EwonBaseApplication
from ewon_common.tags import transform_tag_name

from .app_config import DMConfig
from .app_ui import DMTags, DMUI
from .client import DataMailboxClient
from .m2web import M2WebClient, M2WebException

log = logging.getLogger(__name__)

# The Ewon picks up a write on its next Modbus poll, so the first readback is often stale.
READBACK_ATTEMPTS = 4
READBACK_INTERVAL = 2


def parse_number(value) -> int | float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number.is_integer() else number


class DMApplication(EwonBaseApplication):
    config_cls = DMConfig
    tags_cls = DMTags
    ui_cls = DMUI

    m2web: M2WebClient | None = None

    async def setup(self):
        tz = self.resolve_tz()
        self.device = DataMailboxClient(
            self.config.dm_token.value,
            self.config.dm_developer_id.value,
            tz,
            self.config.ewon_id.value,
            self.config.ewon_name.value,
        )
        await self.device.setup()
        await self.tags.warning_hidden.set(True)

        self.write_points = {
            p.point.value: p for p in self.config.write_points.elements
        }
        if self.write_points:
            # Point names come from config, so they can't use the @handler decorator.
            # A point with a UI control must be claimed by the UI manager, or its default
            # handler would answer "success" before the write happens.
            for name in self.write_points:
                manager = (
                    self.ui_manager
                    if name in self.ui_manager._interactions
                    else self.rpc
                )
                manager._handlers[("ui_cmds", name)] = (None, self.on_write)

            self.m2web = M2WebClient(
                self.config.t2m_account.value,
                self.config.t2m_username.value,
                self.config.t2m_password.value,
                self.config.dm_developer_id.value,
                self.config.ewon_name.value,
                self.config.ewon_username.value,
                self.config.ewon_password.value,
            )
            await self.m2web.setup()

    async def close(self):
        await super().close()
        if self.m2web:
            await self.m2web.close()

    async def fetch(self):
        self.device.last_transaction_id = self.tags.last_ewon_transaction_id.value
        log.info(f"Last transaction id: {self.device.last_transaction_id}")
        await self.device.sync_data(create_transaction=True)

        await self.device.create_frames()
        await self.process_frames()

        if self.device.last_transaction_id is not None:
            await self.tags.last_ewon_transaction_id.set(
                self.device.last_transaction_id
            )

        if self.device.ewon_id != self.config.ewon_id.value:
            await self.api.update_channel_aggregate(
                "deployment_config",
                {
                    "applications": {
                        self.app_key: {self.config.ewon_id._name: self.device.ewon_id}
                    }
                },
            )

    async def on_write(self, ctx, request):
        point = self.write_points[ctx.method]
        tag_name = point.tag_name.value

        expires_after = ctx.message.data.get("expires_after")
        if expires_after is not None:
            age = datetime.now(UTC) - ctx.message.timestamp
            if age > timedelta(milliseconds=expires_after):
                raise RPCError(
                    "EXPIRED",
                    f"Command expired {age.total_seconds():.0f}s after it was sent",
                )

        # The panel cancels by patching the message, which a create event doesn't carry.
        latest = await self.api.fetch_message("ui_cmds", ctx.message.id)
        if (latest.data.get("status") or {}).get("code") == "error":
            raise RPCError("CANCELLED", "Command was cancelled before it ran")

        if point.fixed_value.value is not None:
            value = parse_number(point.fixed_value.value)
        elif isinstance(request, bool):
            value = int(request)
        else:
            value = parse_number(request)
        if value is None:
            raise RPCError("INVALID", f"{request!r} is not a number")

        if (point.min_value.value is not None and value < point.min_value.value) or (
            point.max_value.value is not None and value > point.max_value.value
        ):
            raise RPCError(
                "OUT_OF_RANGE",
                f"{value} is outside {point.min_value.value} to {point.max_value.value}",
            )

        await ctx.acknowledge()
        log.info(f"Writing {tag_name} = {value} for {ctx.method}")
        try:
            await self.m2web.write_tags({tag_name: value})

            # A button's bit may already be cleared by the PLC, so only setpoints are read back.
            if point.fixed_value.value is not None:
                return {"tag": tag_name, "value": value}

            readback = None
            for attempt in range(READBACK_ATTEMPTS):
                if attempt:
                    await asyncio.sleep(READBACK_INTERVAL)
                readback = parse_number((await self.m2web.read_tags()).get(tag_name))
                if readback == value:
                    break
        except (M2WebException, aiohttp.ClientError, TimeoutError) as e:
            raise RPCError("EWON_ERROR", str(e) or type(e).__name__) from e

        if readback is not None:
            shown = bool(readback) if point.ui_control.value == "Switch" else readback
            await self.record_readback(transform_tag_name(tag_name), shown)

        if readback != value:
            raise RPCError(
                "NOT_CONFIRMED",
                f"Wrote {value} to {tag_name} but the Ewon reads {readback}",
            )
        return {"tag": tag_name, "value": readback}

    async def record_readback(self, key: str, value):
        # Same tag the DataMailbox fetch fills, so the panel sees the write straight away.
        # ``written_at`` stops older DataMailbox frames putting the old value back.
        written_at = dict(self.get_tag("written_at") or {})
        written_at[key] = int(datetime.now(UTC).timestamp() * 1000)
        await self.set_tag(key, value)
        await self.set_tag("written_at", written_at)
        await self.tag_manager.commit_tags()
        # Log just this value: a record_log commit would log every tag at wall-clock time.
        await self.api.create_message("tag_values", {self.app_key: {key: value}})
