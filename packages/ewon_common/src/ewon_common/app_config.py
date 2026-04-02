import zoneinfo

from pydoover import config
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
    data_type = config.Enum(
        "Data Type", choices=["Numeric", "Text", "Boolean"], default="Numeric"
    )
    transformation = config.String("Transformation", default=None)


class EwonCommonConfig(config.Schema):
    subscription = SubscriptionConfig()
    schedule = ScheduleConfig()

    ewon_clock_tz = config.Enum(
        "Ewon Clock Timezone",
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
        "Tags",
        element=TagConfig("Tag Config"),
        description="Tags to include in the UI.",
    )
    exclude = config.Array(
        "Exclude",
        element=config.String("Tag Name"),
        description="Tags to exclude from the UI.",
    )
