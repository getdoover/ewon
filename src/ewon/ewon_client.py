import itertools
import logging
from typing import Any
from zoneinfo import ZoneInfo

import aiohttp

from datetime import datetime

from .tags import TagFrame, Tag, TagValue

log = logging.getLogger(__name__)

# pydatamailbox:
# 1. uses requests (we want aiohttp / async friendly library)
# 2. hasn't received an update in 4 years
# 3. isn't doing much for us.


class Talk2MException(Exception):
    pass


class Talk2MClient:
    BASE_URL = "https://data.talk2m.com/"

    def __init__(self, token: str, developer_id: str):
        self.session = None
        self.extra_data = {
            "t2mdevid": developer_id,
            "t2mtoken": token,
        }

    async def setup(self):
        self.session = aiohttp.ClientSession()

    async def close(self):
        await self.session.close()

    async def _request(self, endpoint: str, data: dict | None = None):
        data = data or {}
        data.update(**self.extra_data)

        async with self.session.post(self.BASE_URL + endpoint, data=data) as response:
            if response.status != 200:
                raise Talk2MException(f"Failed to get data: {response.status}")

            return await response.json()

    async def get_status(self):
        return await self._request("getstatus")

    async def get_ewons(self):
        return await self._request("getewons")

    async def get_ewon(self, ewon_id: int | None, ewon_name: str | None = None):
        if not ewon_id and not ewon_name:
            raise Talk2MException("id and name cannot be null in the same time")

        data = {}
        if ewon_id:
            data["id"] = ewon_id
        elif ewon_name:
            data["name"] = ewon_name

        return await self._request("getewon", data)

    async def sync_data(
        self,
        last_transaction_id: str = None,
        create_transaction: bool = True,
        ewon_ids: list[int] = None,
    ):
        data: dict[str, Any] = {"createTransaction": create_transaction}
        if last_transaction_id:
            data["lastTransactionId"] = last_transaction_id
        if ewon_ids:
            data["ewonIds"] = ",".join(str(ewon_id) for ewon_id in ewon_ids)

        return await self._request("syncdata", data)


def truncate_timestamp(timestamp: datetime):
    truncated_minute = timestamp.minute % 5
    return timestamp.replace(
        microsecond=0, second=0, minute=timestamp.minute - truncated_minute
    )


class EwonClient:
    def __init__(
        self,
        dm_token: str,
        dm_dev_id: str,
        clock_tz: ZoneInfo,
        ewon_id: int,
        ewon_name: str | None = None,
    ):
        self.ewon_id = ewon_id
        self.ewon_name = ewon_name

        self.last_transaction_id = None
        self.clock_tz = clock_tz

        self.client = Talk2MClient(dm_token, dm_dev_id)

        self.tags_by_id: dict[int, Tag] = {}
        self.tags_by_name: dict[str, Tag] = {}
        self.tags: list[Tag] = []

        self.tag_frames: list[TagFrame] = []

    async def setup(self):
        await self.client.setup()
        await self.fetch()

    async def close(self):
        await self.client.close()

    async def fetch(self):
        # allows for a None or 0 value
        if not self.ewon_id:
            log.info(f"Fetching Ewon {self.ewon_name}")
            data = await self.client.get_ewon(self.ewon_id, self.ewon_name)
            self.update_from_ewon(data)
        else:
            log.info("Already have Ewon ID, skipping...")

    async def sync_data(self, create_transaction: bool = None):
        if self.last_transaction_id is None and create_transaction is None:
            create_transaction = True
        else:
            create_transaction = create_transaction or False

        data = await self.client.sync_data(
            self.last_transaction_id,
            create_transaction,
            [self.ewon_id],
        )

        self.last_transaction_id = data.get("transactionId")
        try:
            ewon_data = data["ewons"]
        except KeyError:
            pass
        else:
            if len(ewon_data) > 0:
                self.update_from_ewon(ewon_data[0])

    def update_from_ewon(self, data: dict):
        if (self.ewon_id and str(self.ewon_id) != str(data["id"])) or (
            self.ewon_name and str(self.ewon_name) != str(data["name"])
        ):
            log.warning(
                f"Payload: {data} does not match our recorded ewon name "
                f"('{self.ewon_name}') or id ('{self.ewon_id}'). Skipping..."
            )
            return

        ## get the ewon data
        self.ewon_id = data.get("id")
        self.ewon_name = data.get("name")

        self.tags_by_id.clear()
        self.tags_by_name.clear()
        self.tags = []

        for payload in data.get("tags", []):
            tag = Tag.from_dict(payload, self.clock_tz)

            # pre-compute our tag lookups
            self.tags_by_id[tag.tag_id] = tag
            self.tags_by_name[tag.tag_name] = tag
            self.tags.append(tag)

    async def create_frames(self):
        # if self.tags is None:
        #     await self.sync_data()

        log.info(f"Creating frames for ewon {self.ewon_id}")

        self.tag_frames.clear()
        # flatten all tag values into a single list
        vals: list[TagValue] = list(
            itertools.chain.from_iterable([tag.values for tag in self.tags])
        )
        vals.sort(key=lambda t: t.timestamp)

        # group tags by nearest 5min and call that a "frame"
        current_run = []
        for tag_value in vals:
            if (
                current_run
                and abs(
                    int(
                        (tag_value.timestamp - current_run[0].timestamp).total_seconds()
                    )
                )
                >= 300
            ):
                self.tag_frames.append(
                    TagFrame(timestamp=current_run[0].timestamp, tag_values=current_run)
                )
                current_run = []

            current_run.append(tag_value)

        if len(current_run) > 0:
            self.tag_frames.append(
                TagFrame(timestamp=current_run[0].timestamp, tag_values=current_run)
            )

    def get_tag(self, tag_id: int):
        try:
            return self.tags_by_id[tag_id]
        except KeyError:
            return None

    def get_tag_named(self, tag_name: str):
        try:
            return self.tags_by_name[tag_name]
        except KeyError:
            return None
