import logging
from datetime import timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydoover.cloud.processor import ProcessorBase

from netbiter_argos_client import Netbiter

from ui import NetBiterUI


log = logging.getLogger()


class target(ProcessorBase):
    def setup(self):
        self.ui_state_channel = self.fetch_channel_named("ui_state")
        self.ui_cmds_channel = self.fetch_channel_named("ui_cmds")

        tag_names = [
            t["tag_name"]
            for t in self.ui_config.get("tags", [])
            if t["tag_name"] not in self.ui_config.get("exclude", [])
        ]

        self.device = Netbiter(
            self.api_token,
            self.device_id,
            tag_names,
        )
        self.device.set_clock_tz(self.device_clock_tz)
        self.device.update()

        # Construct the UI
        self.ui = NetBiterUI(self.ui_config)
        self.ui_manager.add_children(*self.ui.fetch())
        self.ui_manager.pull()

    def process(self):
        message_type = self.package_config.get("message_type")

        if message_type == "DEPLOY":
            self.on_deploy()
        elif message_type == "DOWNLINK":
            self.on_downlink()
        elif message_type == "FETCH":
            self.on_fetch()

    @property
    def api_token(self):
        return self.get_agent_config("API_TOKEN")

    @property
    def developer_id(self):
        return self.get_agent_config("DEVELOPER_ID")

    @property
    def device_id(self):
        return self.get_agent_config("DEVICE_ID")

    @property
    def device_name(self):
        return self.get_agent_config("DEVICE_NAME")

    @property
    def device_clock_tz(self) -> ZoneInfo:
        tz_string = self.get_agent_config("DEVICE_CLOCK_TZ")

        tz_obj = timezone.utc

        if tz_string:
            try:
                # tz_obj = tz.gettz(tz_string)
                tz_obj = ZoneInfo(tz_string)
            except ZoneInfoNotFoundError:
                log.error(f"Invalid timezone string: {tz_string}")

        return tz_obj

    @property
    def ui_config(self):
        return self.get_agent_config("UI_CONFIG")

    def on_deploy(self):
        ## Run any deployment code here

        # Construct the UI
        self.ui_manager.push(record_log=False, even_if_empty=True)

        # Trigger a fetch
        self.on_fetch()

    def on_downlink(self):
        # Run any downlink processing code here
        pass

    def on_fetch(self):
        ## Get the last transaction id, if any from ui_cmds
        last_transaction_id = None
        ui_cmds_agg = self.ui_cmds_channel.fetch_aggregate()
        if ui_cmds_agg is not None:
            cmds = ui_cmds_agg.get("cmds")
            if cmds is not None:
                last_transaction_id = cmds.get("last_device_transaction_id")

        log.info(f"Last transaction id: {last_transaction_id}")

        ## Get the latest data from the device
        self.device.last_transaction_id = last_transaction_id
        self.device.syncdata(create_transaction=True)

        ## Create the frames for the UI
        self.device.create_frames()

        self.ui.update(self.device)
        if self.ui.error.hidden is False:
            log.error(f"Device error: {self.ui.error.display_name}")
            self.ui_manager.add_children(self.ui.error)

        self.ui_manager.push(
            record_log=True, even_if_empty=True, publish_fields=["currentValue"]
        )

        ## if success, get the latest transaction id and update the ui_cmds channel
        if self.device.last_transaction_id is not None:
            self.ui_cmds_channel.publish(
                {"cmds": {"last_device_transaction_id": self.device.last_transaction_id}}
            )
