"""Timestamp handling for the DataMailbox client.

The DMWeb API reports ``date`` values as ISO-8601 strings with a ``Z`` suffix
regardless of how the Ewon logs them. Only when the Ewon has "Record data in
UTC" enabled are they actually UTC, and the feed then carries a ``timeZone``
field. Otherwise they are the Ewon's local clock and must be interpreted in the
configured clock timezone.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from data_mailbox.client import DataMailboxClient

ADELAIDE = ZoneInfo("Australia/Adelaide")


def _payload(**extra):
    payload = {
        "id": 1753354,
        "name": "Anglesea",
        "tags": [
            {
                "id": 14626287,
                "name": "Gas_Flow",
                "dataType": "Float",
                "description": "Gas Flow",
                "history": [{"date": "2026-09-13T22:20:56Z", "value": 99.5}],
            }
        ],
        "lastSynchroDate": "2026-09-13T22:28:23Z",
    }
    payload.update(extra)
    return payload


def _client():
    return DataMailboxClient("token", "dev-id", ADELAIDE, None, "Anglesea")


def test_local_clock_ewon_uses_configured_timezone():
    client = _client()
    client.update_from_ewon(_payload())

    assert client.records_in_utc is False
    (value,) = client.get_tag_named("Gas_Flow").values
    # Wall-clock 22:20:56 on an Adelaide clock == 12:50:56 UTC (UTC+9:30).
    assert value.timestamp == datetime(2026, 9, 13, 12, 50, 56, tzinfo=timezone.utc)


def test_utc_recording_ewon_ignores_configured_timezone():
    client = _client()
    client.update_from_ewon(_payload(timeZone="Australia/Melbourne"))

    assert client.records_in_utc is True
    (value,) = client.get_tag_named("Gas_Flow").values
    assert value.timestamp == datetime(2026, 9, 13, 22, 20, 56, tzinfo=timezone.utc)


def test_mode_follows_each_payload():
    """A swapped unit can flip the flag; the client must not latch the old mode."""
    client = _client()
    client.update_from_ewon(_payload(timeZone="Australia/Melbourne"))
    assert client.records_in_utc is True

    client.update_from_ewon(_payload())
    assert client.records_in_utc is False


@pytest.mark.asyncio
async def test_frames_are_built_from_corrected_timestamps():
    client = _client()
    client.update_from_ewon(
        _payload(
            timeZone="Australia/Melbourne",
            tags=[
                {
                    "id": 1,
                    "name": "Gas_Flow",
                    "dataType": "Float",
                    "history": [
                        {"date": "2026-09-13T22:05:56Z", "value": 1.0},
                        {"date": "2026-09-13T22:20:56Z", "value": 2.0},
                    ],
                },
                {
                    "id": 2,
                    "name": "Temperature",
                    "dataType": "Float",
                    "history": [{"date": "2026-09-13T22:20:56Z", "value": 700.0}],
                },
            ],
        )
    )
    await client.create_frames()

    assert [f.timestamp for f in client.tag_frames] == [
        datetime(2026, 9, 13, 22, 5, 56, tzinfo=timezone.utc),
        datetime(2026, 9, 13, 22, 20, 56, tzinfo=timezone.utc),
    ]
    assert sorted(v.tag_name for v in client.tag_frames[1].tag_values) == [
        "Gas_Flow",
        "Temperature",
    ]
