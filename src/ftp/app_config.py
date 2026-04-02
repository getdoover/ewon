from pathlib import Path

from pydoover import config

from ewon_common import EwonCommonConfig


class FTPConfig(EwonCommonConfig):
    ftp_server = config.String("FTP Server")
    ftp_username = config.String("FTP Username")
    ftp_password = config.String("FTP Password")
    ftp_file_name = config.String("FTP File Name")


def export():
    FTPConfig.export(
        Path(__file__).parents[2] / "doover_config.json", "ewon_processor_ftp"
    )
