from pathlib import Path

from pydoover import config

from ewon_common import EwonCommonConfig


class NetbiterConfig(EwonCommonConfig):
    netbiter_access_key = config.String("Netbiter Access Key")
    netbiter_system_id = config.String("Netbiter System ID")


def export():
    NetbiterConfig.export(
        Path(__file__).parents[2] / "doover_config.json", "ewon_processor_netbiter"
    )
