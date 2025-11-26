import csv
import logging
from datetime import datetime

from pydoover.ui import Colour

from pydoover import ui

from pydoover.cloud.processor import ProcessorBase

import ftplib


def construct_ui():
    return (
        ui.Multiplot(
            "multiplot",
            "Multiplot",
            series=["ch4", "temperature", "main_gas_valve", "power_on"],
            series_active=[True, True, False, False],
            series_colours=[Colour.blue, Colour.yellow, Colour.green, Colour.red],
        ),
        ui.NumericVariable("ch4", "CH4 Concentration (%v/v)", precision=2),
        ui.NumericVariable("temperature", "Temperature (°C)", precision=2),
        ui.BooleanVariable("main_gas_valve", "Main Gas Valve On"),
        ui.BooleanVariable("power_on", "Power On"),
        ui.ConnectionInfo(
            "connectionInfo",
            connection_type=ui.ConnectionType.periodic,
            connection_period=(30 * 60),  # 1 hour
            next_connection=(30 * 60),  # 1 hour
            allowed_misses=6,
        ),
    )


class target(ProcessorBase):
    def setup(self):
        # Get the required channels
        self.ui_state_channel = self.api.create_channel("ui_state", self.agent_id)
        self.ui_cmds_channel = self.api.create_channel("ui_cmds", self.agent_id)

        # Construct the UI
        self._ui_elements = construct_ui()
        self.ui_manager.set_children(self._ui_elements)

        self.ui_manager.agent_id = self.agent_id
        self.ui_manager.app_wrap_ui = False
        self.ui_manager.pull()

    def process(self):
        message_type = self.package_config.get("message_type")

        if message_type == "DEPLOY":
            self.on_deploy()
        elif message_type == "DOWNLINK":
            self.on_downlink()
        elif message_type == "FETCH":
            self.on_fetch()

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
        server = ftplib.FTP(self.get_agent_config("FTP_SERVER"))
        server.login(
            self.get_agent_config("FTP_USERNAME"), self.get_agent_config("FTP_PASSWORD")
        )

        name = self.get_agent_config("FTP_FILE_NAME")
        with open("/tmp/ewon_ftp.csv", "wb") as fp:
            server.retrbinary(f"RETR {name}", fp.write)

        server.quit()

        # parse the data
        with open("/tmp/ewon_ftp.csv", "r") as file:
            csv_reader = csv.DictReader(file)
            data = list(csv_reader)

        if len(data) == 0:
            logging.info("No data in file")
            return

        # check if we've already processed the file, process otherwise.
        max_ts = max([datetime.fromisoformat(d["Date"]) for d in data]).timestamp()

        last_transaction_id = None
        ui_cmds_agg = self.ui_cmds_channel.aggregate
        if ui_cmds_agg is not None:
            cmds = ui_cmds_agg.get("cmds")
            if cmds is not None:
                last_transaction_id = cmds.get("last_ewon_transaction_id")

        if last_transaction_id is not None and max_ts < last_transaction_id:
            logging.info(
                f"Skipping fetch, last transaction id: {last_transaction_id}, max ts: {max_ts}"
            )
            return

        # Serial Number	Date	Slave ID	Register Address	Value	Channel Index
        # 21115024330091	2025-11-26 13:39:20	1	0	16443	1
        # 21115024330091	2025-11-26 13:39:22	1	1	16900	2
        # 21115024330091	2025-11-26 13:39:23	1	0	0	3
        # 21115024330091	2025-11-26 13:39:24	1	1	1	4
        # 21115024330091	2025-11-26 13:44:24	1	0	16435	1
        lookup = {
            1: "ch4",
            2: "temperature",
            3: "main_gas_valve",
            4: "power_on",
        }
        for row in data:
            ts = datetime.fromisoformat(row["Date"])
            if last_transaction_id and ts.timestamp() < last_transaction_id:
                continue

            try:
                name = lookup[int(row["Channel Index"])]
            except KeyError:
                logging.info(f"Skipping key '{name}'")
                continue

            value = int(row["Value"])
            if name == "ch4":
                # from eagle.io
                value = round(value * 0.003052 - 50, 2)
            elif name == "temperature":
                value = round(value * 0.039673 - 650, 2)
            else:
                value = bool(value)

            self.ui_manager.update_variable(name, value)
            self.ui_manager.push(
                record_log=True,
                timestamp=ts,
                even_if_empty=True,
                publish_fields=["currentValue"],
            )
            self.ui_cmds_channel.publish(
                {"cmds": {"last_ewon_transaction_id": ts.timestamp()}}
            )
