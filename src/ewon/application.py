import logging
from datetime import timedelta, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydoover.processor import Application
from pydoover.models import (
    ScheduleEvent,
    MessageCreateEvent,
    DeploymentEvent,
)

from .app_config import EwonConfig
from .app_tags import EwonTags
from .app_ui import EwonUI
from .ewon_client import EwonClient

log = logging.getLogger()


class EwonApplication(Application):
    config_cls = EwonConfig
    tags_cls = EwonTags
    ui_cls = EwonUI

    async def setup(self):
        try:
            tz = ZoneInfo(self.config.ewon_clock_tz.value)
        except ZoneInfoNotFoundError:
            log.info(
                f"Zone info {self.config.ewon_clock_tz.value} not found. Defaulting to Australia/Brisbane."
            )
            tz = ZoneInfo("Australia/Brisbane")

        self.device = EwonClient(
            self.config.dm_token.value,
            self.config.dm_developer_id.value,
            tz,
            self.config.ewon_id.value,
            self.config.ewon_name.value,
        )
        await self.device.setup()

    async def close(self):
        await self.device.close()

    async def on_message_create(self, message: MessageCreateEvent):
        await self.fetch()

    async def on_deploy(self, deployment: DeploymentEvent):
        # Trigger a fetch
        await self.fetch()

    async def on_schedule(self, event: ScheduleEvent):
        await self.fetch()

    async def fetch(self):
        ## Get the latest data from the ewon
        self.device.last_transaction_id = self.tags.last_ewon_transaction_id.value
        log.info(f"Last transaction id: {self.device.last_transaction_id}")
        await self.device.sync_data(create_transaction=True)

        ## Create the frames for the UI
        await self.device.create_frames()

        ## For each frame, publish a timestamped message to the ui_state channel
        for frame in self.device.tag_frames:
            timestamp = frame.timestamp
            for tag in frame.tag_values:
                await self.set_tag(tag.tag_name, tag.value)

            log.info(
                f"Pushing record log for timestamp: {timestamp}, with tz {timestamp.tzinfo}"
            )
            await self.tag_manager.commit_tags(timestamp=timestamp)

            # fix for now since doover data is limited on staging atm
            # await asyncio.sleep(1)

        # if success, get the latest transaction id and update the tags channel
        if self.device.last_transaction_id is not None:
            await self.tags.last_ewon_transaction_id.set(
                self.device.last_transaction_id
            )

        if self.device.ewon_id != self.config.ewon_id.value:
            # if we fetched an ewon ID and don't currently have one set, update the deployment config.
            # this saves ~300ms each time we fetch the data.
            await self.api.update_channel_aggregate(
                "deployment_config",
                {
                    "applications": {
                        self.app_key: {self.config.ewon_id._name: self.device.ewon_id}
                    }
                },
            )

        # update device as being online
        # expect it to next be online in 15min from last reading
        # allow a few misses (6) before marking it offline.
        last_ping: datetime | None = (
            max(t.timestamp for t in self.device.tag_frames)
            if self.device.tag_frames
            else None
        )
        if last_ping:
            await self.ping_connection(
                last_ping,
                offline_at=last_ping + timedelta(minutes=90),
            )
