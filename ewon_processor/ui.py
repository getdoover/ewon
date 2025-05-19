from contextlib import suppress
from typing import TYPE_CHECKING, Any

from pydoover import ui

if TYPE_CHECKING:
    from netbiter_argos_client import Netbiter, Tag


def tag_to_element(config: dict[str, Any], tag: "Tag"):
    if not tag:
        return None

    if not tag.data_type:
        return None

    name = config.get("tag_name", tag.name)
    display_name = config.get("display_name", tag.description)

    if tag.data_type == "Bool":
        return ui.BooleanVariable(name, display_name)

    # dataType in ("Float", "Int", "UInt")
    return ui.NumericVariable(
        name,
        display_name,
        precision=config.get("dec_precision"),
        ranges=config.get("ranges"),
        form=config.get("form"),
    )


class NetBiterUI:
    def __init__(self, config: dict[str, Any], device: "Netbiter") -> None:
        multiplots = config.get("multiplots", [])
        with suppress(KeyError):
            multiplots.append(config["multiplot"])

        self.multiplots = [
            ui.Multiplot(
                p.get("name", f"multiplot{i}"),
                p.get("title", None),
                series=p["series"],
                series_active=p["default_active"],
                series_colours=p["series_colours"],
            )
            for i, p in enumerate(multiplots)
        ]

        exclude = config.get("exclude", [])
        tags = [t for t in config.get("tags", []) if t["tag_name"] not in exclude]
        auto_include = config.get("auto_include", True)

        self.tags = []
        for tag in tags:
            elem = tag_to_element(tag, device.get_tag(tag["tag_name"]))
            if elem is None and auto_include:
                elem = tag_to_element({}, device.get_tag(tag["tag_name"]))

            if elem is not None:
                self.tags.append(elem)

        self.error = ui.WarningIndicator("error", "placeholder", hidden=True)
        self.connection_info = ui.ConnectionInfo(
            "connectionInfo",
            connection_type=ui.ConnectionType.periodic,
            connection_period=60 * 60,  # 1 hour
            next_connection=60 * 60,  # 1 hour
            allowed_misses=6,
        )

    def fetch(self):
        return *self.multiplots, *self.tags, self.error, self.connection_info

    def update(self, device: "Netbiter") -> bool:
        if device.error:
            self.error.display_name = str(device.error)
            self.error.hidden = False
            return False

        else:
            self.error.hidden = True

        ok = False
        for tag in self.tags:
            tag_value = device.get_tag(tag.name)
            if tag_value is not None:
                tag.update(tag_value.value)
                ok = True

        return ok
