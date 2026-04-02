from pathlib import Path

from pydoover import config

from ewon_common import EwonCommonConfig


class DMConfig(EwonCommonConfig):
    dm_token = config.String("Data Mailbox API Token")
    dm_developer_id = config.String("Data Mailbox Developer ID")
    ewon_id = config.Integer("Ewon ID", default=None)
    ewon_name = config.String("Ewon Name")


def export():
    DMConfig.export(
        Path(__file__).parents[2] / "doover_config.json", "ewon_processor"
    )
