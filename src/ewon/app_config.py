import zoneinfo
from pathlib import Path

from pydoover import config, ui
from pydoover.ui import Colour
from pydoover.cloud.processor import ScheduleConfig, SubscriptionConfig


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
    def __init__(self, display_name: str = "Series Element"):
        super().__init__(display_name)

        self.name = config.String("Name")
        self.colour = config.Enum("Colour", choices=ALL_COLOURS, default=Colour.blue)
        self.active = config.Boolean("Active", default=True)


class MultiplotConfig(config.Object):
    def __init__(self, display_name: str = "Multiplot Config"):
        super().__init__(display_name)

        self.title = config.String("Title")
        self.series = config.Array("Series Elements", element=SeriesConfig())


class TagConfig(config.Object):
    def __init__(self, display_name: str = "Tag"):
        super().__init__(display_name)

        self.tag_name = config.String("Tag Name")
        self.tag_display_name = config.String("Display Name")
        self.precision = config.Integer("Decimal Precision", default=2)

    def to_ui_element(self):
        # I haven't added support for bools / ints / etc. since they don't seem to be used atm.
        return ui.NumericVariable(
            self.tag_name.value,
            self.tag_display_name.value,
            precision=self.precision.value,
        )


class EwonConfig(config.Schema):
    def __init__(self):
        self.subscription = SubscriptionConfig()
        self.schedule = ScheduleConfig()

        # self.auto_include = config.Boolean("Auto Include Tags")
        self.dm_token = config.String("Data Mailbox API Token")
        self.dm_developer_id = config.String("Data Mailbox Developer ID")
        self.ewon_id = config.Integer("Ewon ID")
        self.ewon_name = config.String("Ewon Name")
        self.ewon_clock_tz = config.Enum(
            "Ewon Clock Timezone",
            # only show Australian timezones. This still has heaps?? (e.g. Lord Howe, etc.)
            choices=list(sorted([z for z in zoneinfo.available_timezones() if "Australia" in z])),
            default="Australia/Brisbane",
        )

        self.multiplots = config.Array(
            "Multiplots",
            element=MultiplotConfig(),
            description="Multiplots to include in the UI.",
        )
        self.tags = config.Array(
            "Tags", element=TagConfig(), description="Tags to include in the UI."
        )
        self.exclude = config.Array(
            "Exclude",
            element=config.String("Tag Name"),
            description="Tags to exclude from the UI.",
        )


def export():
    EwonConfig().export(
        Path(__file__).parents[2] / "doover_config.json", "ewon_processor"
    )
