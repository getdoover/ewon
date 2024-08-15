import logging, json, time
from datetime import datetime, timezone, timedelta

from pydoover.cloud import ProcessorBase

from data_mailbox_client import DataMailboxClient, Ewon

from ui import construct_ui



class target(ProcessorBase):


    def setup(self):

        # Get the required channels
        self.ui_state_channel = self.api.create_channel("ui_state", self.agent_id)
        self.ui_cmds_channel = self.api.create_channel("ui_cmds", self.agent_id)

        # Construct the UI
        self._ui_elements = construct_ui(self, self.get_ewon())
        self.ui_manager.set_children(self._ui_elements)
        self.ui_manager.pull()


    def process(self):
        message_type = self.package_config.get("message_type")

        if message_type == "DEPLOY":
            self.on_deploy()
        elif message_type == "DOWNLINK":
            self.on_downlink()
        elif message_type == "UPLINK":
            self.on_uplink()

    def get_ewon(self):
        if hasattr(self, "_ewon"):
            return self._ewon
        
        ## Setup the ewon interface
        self._dm_client = DataMailboxClient(token=self.get_dm_token(), devid=self.get_developer_id())
        self._ewon = Ewon(client=self._dm_client, ewon_id=self.get_ewon_id())
        self._ewon.update()

        return self._ewon

    def get_dm_token(self):
        return self.get_agent_config("DM_TOKEN")
    
    def get_developer_id(self):
        return self.get_agent_config("DEVELOPER_ID")

    def get_ewon_id(self):
        return self.get_agent_config("EWON_ID")

    def get_ewon_ui_settings(self):
        return self.get_agent_config("EWON_UI_SETTINGS")

    def on_deploy(self):
        ## Run any deployment code here

        # Construct the UI
        self.ui_manager.push()

        # Trigger an uplink
        self.on_uplink()


    def on_downlink(self):
        # Run any downlink processing code here
        pass

    def on_uplink(self):

        ## Get the last transaction id, if any from ui_cmds
        last_transaction_id = None
        ui_cmds_agg = self.ui_cmds_channel.aggregate
        if ui_cmds_agg is not None:
            cmds = ui_cmds_agg.get("cmds")
            if cmds is not None:
                last_transaction_id = cmds.get("last_ewon_transaction_id")

        ## Get the latest data from the ewon
        self.get_ewon().last_transaction_id = last_transaction_id
        self.get_ewon().syncdata()

        ## Create the frames for the UI
        self.get_ewon().create_frames()

        ## For each frame, publish a timestamped message to the ui_state channel
        for frame in self.get_ewon().tag_frames:

            timestamp = frame.timestamp
            for tag in frame.tags:
                self.ui_manager.update_variable(tag.tag_name, tag.current_value)
            
            self.ui_manager.push(record_log=True, timestamp=timestamp, even_if_empty=True)

        ## if success, get the latest transaction id and update the ui_cmds channel
        if self.get_ewon().last_transaction_id is not None:
            self.ui_cmds_channel.publish({
                "cmds": {
                    "last_ewon_transaction_id": self.get_ewon().last_transaction_id
                }
            })
