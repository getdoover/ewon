import logging

from ewon_common import EwonBaseApplication

from .app_config import NetbiterConfig
from .client import NetbiterClient

log = logging.getLogger(__name__)


class NetbiterApplication(EwonBaseApplication):
    config_cls = NetbiterConfig

    async def setup(self):
        tz = self.resolve_tz()
        self.device = NetbiterClient(
            access_key=self.config.netbiter_access_key.value,
            system_id=self.config.netbiter_system_id.value,
            parameter_names=[t.tag_name.value for t in self.config.tags.elements],
            clock_tz=tz,
        )
        await self.device.setup()
        await self.tags.warning_hidden.set(True)

    async def fetch(self):
        await self.device.sync_data()
        await self.device.create_frames()
        await self.process_frames()
