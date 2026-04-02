import logging
from datetime import timedelta, datetime
from typing import Any
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

    def _get_transformed_tags(self):
        return [
            t for t in self.config.tags.elements
            if t.transformation.value is not None
        ]

    async def process_frames(self):
        transformed_tags = self._get_transformed_tags()

        for frame in self.device.tag_frames:
            timestamp = frame.timestamp
            updated: dict[str, Any] = {}

            for tag in frame.tag_values:
                await self.set_tag(tag.tag_name, tag.value)
                updated[tag.tag_name] = tag.value

            for tag in transformed_tags:
                name = tag.tag_name.value
                operation = tag.transformation.value

                if not any(k in operation for k in updated):
                    log.info(f"Ignoring computed tag: {name}")
                    continue

                for tag_name, tag_value in updated.items():
                    operation = operation.replace(
                        "{" + tag_name + "}", str(tag_value)
                    )

                try:
                    result = eval(operation)
                except Exception as e:
                    log.info(
                        f"Failed to compute {name} transformed tag "
                        f"({operation}) - original: "
                        f"{tag.transformation.value}: {e}."
                    )
                else:
                    log.info(f"Computed tag - {name}: {result}")
                    await self.set_tag(name, result)

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
