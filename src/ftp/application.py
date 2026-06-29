import logging

from ewon_common import EwonBaseApplication

from .app_config import FTPConfig
from .client import FTPClient

log = logging.getLogger(__name__)


class FTPApplication(EwonBaseApplication):
    config_cls = FTPConfig

    async def setup(self):
        tz = self.resolve_tz()
        self.device = FTPClient(
            server=self.config.ftp_server.value,
            username=self.config.ftp_username.value,
            password=self.config.ftp_password.value,
            file_name=self.config.ftp_file_name.value,
            clock_tz=tz,
        )
        await self.device.setup()
        await self.tags.warning_hidden.set(True)

    async def fetch(self):
        self.device.last_transaction_id = self.tags.last_ewon_transaction_id.value
        log.info(f"Last transaction id: {self.device.last_transaction_id}")

        await self.device.sync_data()
        await self.device.create_frames()
        await self.process_frames()

        if self.device.last_transaction_id is not None:
            await self.tags.last_ewon_transaction_id.set(
                self.device.last_transaction_id
            )
