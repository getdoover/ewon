import logging
from datetime import timedelta, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydoover.processor import Application
from pydoover.models import (
    ScheduleEvent,
    MessageCreateEvent,
    DeploymentEvent,
)

from .app_tags import EwonTags
from .app_ui import EwonUI

log = logging.getLogger(__name__)


class EwonBaseApplication(Application):
    tags_cls = EwonTags
    ui_cls = EwonUI

    device = None

    def resolve_tz(self) -> ZoneInfo:
        try:
            return ZoneInfo(self.config.ewon_clock_tz.value)
        except ZoneInfoNotFoundError:
            log.info(
                f"Zone info {self.config.ewon_clock_tz.value} not found. "
                f"Defaulting to Australia/Brisbane."
            )
            return ZoneInfo("Australia/Brisbane")

    async def close(self):
        await self.device.close()

    async def on_message_create(self, message: MessageCreateEvent):
        await self.fetch()

    async def on_deploy(self, deployment: DeploymentEvent):
        await self.fetch()

    async def on_schedule(self, event: ScheduleEvent):
        await self.fetch()

    async def fetch(self):
        raise NotImplementedError

    async def process_frames(self):
        for frame in self.device.tag_frames:
            timestamp = frame.timestamp
            for tag in frame.tag_values:
                await self.set_tag(tag.tag_name, tag.value)

            log.info(
                f"Pushing record log for timestamp: {timestamp}, "
                f"with tz {timestamp.tzinfo}"
            )
            await self.tag_manager.commit_tags(timestamp=timestamp)

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
