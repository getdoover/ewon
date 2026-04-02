import zoneinfo
from pathlib import Path

from pydoover import config, ui
from pydoover.ui import Colour
from pydoover.processor import ScheduleConfig, SubscriptionConfig


ALL_COLOURS = [
    Colour.blue,
    Colour.green,
    Colour.red,
    Colour.yellow,
    Colour.orange,
    Colour.purple,
    Colour.limegreen,
    Colour.grey,
    Colour.magenta,
    Colour.tomato,
]


class SeriesConfig(config.Object):
    name = config.String("Name")
    colour = config.Enum("Colour", choices=ALL_COLOURS, default=Colour.blue)
    active = config.Boolean("Active", default=True)


class MultiplotConfig(config.Object):
    title = config.String("Title")
    series = config.Array("Series Elements", element=SeriesConfig("Series Config"))


class TagConfig(config.Object):
    tag_name = config.String("Tag Name")
    tag_display_name = config.String("Display Name")
    precision = config.Integer("Decimal Precision", default=2)
    units = config.String("Units", default=None)


class EwonConfig(config.Schema):
    subscription = SubscriptionConfig()
    schedule = ScheduleConfig()

    # auto_include = config.Boolean("Auto Include Tags")
    dm_token = config.String("Data Mailbox API Token")
    dm_developer_id = config.String("Data Mailbox Developer ID")
    ewon_id = config.Integer("Ewon ID", default=None)
    ewon_name = config.String("Ewon Name")
    ewon_clock_tz = config.Enum(
        "Ewon Clock Timezone",
        # only show Australian timezones. This still has heaps?? (e.g. Lord Howe, etc.)
        choices=list(
            sorted([z for z in zoneinfo.available_timezones() if "Australia" in z])
        ),
        default="Australia/Brisbane",
    )

    multiplots = config.Array(
        "Multiplots",
        element=MultiplotConfig("Multiplot Config"),
        description="Multiplots to include in the UI.",
    )
    tags = config.Array(
        "Tags", element=TagConfig("Tag Config"), description="Tags to include in the UI."
    )
    exclude = config.Array(
        "Exclude",
        element=config.String("Tag Name"),
        description="Tags to exclude from the UI.",
    )


def export():
    EwonConfig.export(
        Path(__file__).parents[2] / "doover_config.json", "ewon_processor"
    )
