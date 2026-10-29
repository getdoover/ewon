from pydoover import ui
from pydoover.tags import Tag

from ewon_common import EwonTags, EwonUI
from ewon_common.tags import transform_tag_name

from .app_config import DMConfig


class DMTags(EwonTags):
    config: DMConfig

    async def setup(self):
        await super().setup()
        for p in self.config.write_points.elements:
            key = transform_tag_name(p.tag_name.value)
            if self._get_declaration(key) is None:
                self.add_tag(key, Tag("number"))


class DMUI(EwonUI):
    config: DMConfig

    async def setup(self):
        await super().setup()
        for p in self.config.write_points.elements:
            name = p.point.value
            label = p.label.value or name
            match p.ui_control.value:
                case "Number":
                    # Shows the readback tag, so the field only changes once the Ewon does.
                    tag = self.tags.get_tag(transform_tag_name(p.tag_name.value))
                    self.add_element(
                        ui.FloatInput(
                            label,
                            name=name,
                            value=tag,
                            units=p.units.value or ui.NotSet,
                            min_val=ui.NotSet
                            if p.min_value.value is None
                            else p.min_value.value,
                            max_val=ui.NotSet
                            if p.max_value.value is None
                            else p.max_value.value,
                            requires_confirm=True,
                        )
                    )
                case "Button":
                    self.add_element(ui.Button(label, name=name, requires_confirm=True))
