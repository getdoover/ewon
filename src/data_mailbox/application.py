import logging

from ewon_common import EwonBaseApplication

from .app_config import DMConfig
from .client import DataMailboxClient

log = logging.getLogger(__name__)


class DMApplication(EwonBaseApplication):
    config_cls = DMConfig

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
