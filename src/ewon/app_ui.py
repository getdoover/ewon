from typing import TYPE_CHECKING

from pydoover import ui

from .ewon_client import EwonClient

if TYPE_CHECKING:
    from .app_config import EwonConfig, MultiplotConfig




class EwonUI:
    def __init__(self, config: "EwonConfig") -> None:
        self.multiplots = []
        for i, p in enumerate(config.multiplots.elements):
            p: MultiplotConfig

            # this should really be changed in pydoover / ui but let's just unzip them
            # here for now...
            names = [s.name.value for s in p.series.elements]
            active = [s.active.value for s in p.series.elements]
            colours = [s.colour.value for s in p.series.elements]

            self.multiplots.append(ui.Multiplot(
                f"multiplot-{i}",
                p.title.value,
                series=names,
                series_active=active,
                series_colours=colours,
            ))

        # this whole auto_add thing doesn't make sense because we filter in the device code for
        # only tags that are defined in the UI. Feel free to add it back in...
        # tag_names_set = set(t["tag_name"] for t in tags)
        #
        # if config.get("auto_include", True):
        #     tags += [
        #         {
        #             "tag_name": name,
        #             "display_name": name,
        #         } for name in device_tags if name not in tag_names_set
        #     ]

        excluded = [t.value for t in config.exclude.elements]
        self.tags = [t.to_ui_element() for t in config.tags.elements if t.tag_name.value not in excluded]
        self.error = ui.WarningIndicator("error", "Error", hidden=True)

    def fetch(self):
        return *self.multiplots, *self.tags, self.connection_info

    def update(self, device: "EwonClient") -> bool:
        if device.error:
            self.error.display_name = str(device.error)
            self.error.hidden = False
            return False
        else:
            self.error.hidden = True

        ok = False
        for tag in self.tags:
            tag_value = device.get_tag_named(tag.name)
            if tag_value is not None:
                tag.update(tag_value.value)
                ok = True

        return ok