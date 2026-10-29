from pathlib import Path

from pydoover import config

from ewon_common import EwonCommonConfig


class WritePoint(config.Object):
    point = config.String(
        "Point Name",
        description="ui_cmds command this app answers, e.g. flare_start. Must be unique on the device.",
    )
    tag_name = config.String(
        "Ewon Tag Name", description="The writable Ewon tag behind this point."
    )
    fixed_value = config.Number(
        "Fixed Value",
        default=None,
        description="Always write this value (for buttons). Blank writes the requested value.",
    )
    min_value = config.Number("Minimum", default=None)
    max_value = config.Number("Maximum", default=None)
    label = config.String(
        "Display Name", default=None, description="Label for the UI control."
    )
    ui_control = config.Enum(
        "UI Control",
        choices=["None", "Number", "Button"],
        default="None",
        description="Number edits a setpoint; Button writes the fixed value. None leaves it to other UIs (e.g. the flare panel).",
    )
    units = config.String("Units", default=None)


class DMConfig(EwonCommonConfig):
    dm_token = config.String("Data Mailbox API Token")
    dm_developer_id = config.String("Data Mailbox Developer ID")
    ewon_id = config.Integer("Ewon ID", default=None)
    ewon_name = config.String("Ewon Name")

    # Writes go through M2Web, which doesn't accept API tokens.
    t2m_account = config.String("Talk2M Account", default=None)
    t2m_username = config.String(
        "Talk2M Username",
        default=None,
        description="Talk2M user for M2Web writes. Needs access to this Ewon and no 2FA.",
    )
    t2m_password = config.String("Talk2M Password", default=None)
    ewon_username = config.String(
        "Ewon Username",
        default=None,
        description="Local Ewon user allowed to write tags.",
    )
    ewon_password = config.String("Ewon Password", default=None)
    write_points = config.Array(
        "Write Points",
        element=WritePoint("Write Point"),
        default=[],
        description="Commands this app turns into Ewon tag writes. Leave empty for read-only.",
    )


def export():
    DMConfig.export(Path(__file__).parents[2] / "doover_config.json", "ewon_processor")
