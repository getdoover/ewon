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
                kind = "boolean" if p.ui_control.value == "Switch" else "number"
                self.add_tag(key, Tag(kind))


class DMUI(EwonUI):
    config: DMConfig

    async def setup(self):
        await super().setup()
        points = self.config.write_points.elements
        # Grouped so setpoints come first, then switches, then the command buttons.
        controls = [
            self.make_control(p)
            for control in ("Number", "Switch", "Button")
            for p in points
            if p.ui_control.value == control
        ]
        if controls:
            self.add_element(
                ui.Submodule("Controls", name="controls", children=controls)
            )

    def make_control(self, p):
        name = p.point.value
        label = p.label.value or name
        if p.ui_control.value == "Button":
            return ui.Button(label, name=name, requires_confirm=True)

        # Shows the readback tag, so the control only changes once the Ewon does.
        tag = self.tags.get_tag(transform_tag_name(p.tag_name.value))
        if p.ui_control.value == "Switch":
            return ui.Switch(label, name=name, value=tag, requires_confirm=True)
        return ui.FloatInput(
            label,
            name=name,
            value=tag,
            units=p.units.value or ui.NotSet,
            min_val=ui.NotSet if p.min_value.value is None else p.min_value.value,
            max_val=ui.NotSet if p.max_value.value is None else p.max_value.value,
            requires_confirm=True,
        )
