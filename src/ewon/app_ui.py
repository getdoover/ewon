from pathlib import Path
from typing import TYPE_CHECKING

from pydoover import ui

from .app_tags import EwonTags

if TYPE_CHECKING:
    from .app_config import EwonConfig, MultiplotConfig


class EwonUI(ui.UI):
    config: "EwonConfig"

    async def setup(self):
        for i, p in enumerate(self.config.multiplots.elements):
            p: MultiplotConfig
            series = {
                s.name.value: {"colour": s.colour.value, "active": s.active.value}
                for s in p.series.elements
            }

            self.add_element(ui.Multiplot(p.title.value, series))

        excluded = [t.value for t in self.config.exclude.elements]
        for tag in self.config.tags.value:
            if tag.tag_name.value in excluded:
                continue

            units = tag.units.value or (
                "(" in tag.tag_display_name.value
                and ")" in tag.tag_display_name.value
                and tag.tag_display_name.value.split("(")[1].split(")")[0]
                or None
            )

            self.add_element(
                ui.NumericVariable(
                    tag.tag_display_name.value,
                    value=self.tags.get_tag(tag.tag_name.value),
                    precision=tag.precision.value,
                    units=units,
                )
            )

        self.add_element(
            ui.WarningIndicator(
                name="warning_string",
                display_name=EwonTags.warning_string,
                hidden=EwonTags.warning_active,
            )
        )


def export():
    EwonUI(None, None).export(
        Path(__file__).parents[2] / "doover_config.json", "ewon_processor"
    )
