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
                s.name: {"colour": s.colour, "active": s.active}
                for s in p.series.elements
            }

            self.add_element(ui.Multiplot(p.title, series))

        excluded = [t.value for t in self.config.exclude.elements]
        for tag in self.config.tags:
            if tag.tag_name in excluded:
                continue

            self.add_element(
                ui.NumericVariable(
                    tag.tag_display_name,
                    value=self.tags.get_tag(tag.tag_name),
                    precision=tag.precision,
                )
            )

        self.add_element(
            ui.WarningIndicator(
                name="warning_string",
                display_name=EwonTags.warning_string,
                hidden=EwonTags.warning_active
            )
        )


def export():
    EwonUI(None, None).export(
        Path(__file__).parents[2] / "doover_config.json", "ewon_processor"
    )
