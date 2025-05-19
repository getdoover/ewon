import enum
from datetime import datetime

from typing import Optional, Any

from .misc import Colour

class NotSet:
    pass


class Element:
    type = "uiElement"

    def __init__(
        self,
        name: Optional[str],
        display_name: Optional[str] = None,
        is_available: bool = None,  # not sure of type
        help_str: str = None,
        verbose_str: str = None,
        show_activity: bool = True,
        form: str = None,
        graphic: str = None,  # not sure of type
        layout: str = None,  # not sure of type
        component_url: str = None,  # not sure of type
        position: Optional[int] = None, # 100,
        conditions: Optional[dict] = None,
        **kwargs
    ):
        self.name = name
        self.display_name = display_name or kwargs.get("display_str", None)  # backwards compatibility
        self.is_available = is_available
        self.help_str = help_str
        self.verbose_str = verbose_str
        self.show_activity = show_activity
        self.form = form
        self.graphic = graphic
        self.layout = layout
        self.component_url = component_url
        self.position = position
        self.conditions = conditions

        self._retain_fields = []

    def to_dict(self):
        to_return = {
            "name": self.name,
            "type": self.type,
            "displayString": self.display_name,
            "isAvailable": self.is_available,
            "helpString": self.help_str,
            "verboseString": self.verbose_str,
            "showActivity": self.show_activity,
            "form": self.form,
            "graphic": self.graphic,
            "layout": self.layout,
            "componentUrl": self.component_url,
            "position": self.position,
            "conditions": self.conditions,
        }
        # filter out any null values
        return {k: v for k, v in to_return.items() if v is not None}

    def get_diff(self, other: dict[str, Any], remove: bool = True, retain_fields: Optional[list] = None) -> Optional[dict[str, Any]]:
        this = self.to_dict()

        retain_fields = retain_fields or []
        to_retain = list(set(retain_fields) | set(self._retain_fields))
        # if this == other:
        #     return None

        result = {k: v for k, v in this.items() if other.get(k) != v or k in to_retain}
        if remove:
            result.update(**{k: None for k in other if k not in this and k not in to_retain})  # to_remove
        if len(result) == 0:
            return None

        return result

    ## A stub for the method that will be called when the UI state is updated.
    # The element can choose to update its internal state based on the previous state and the new state.
    def recv_ui_state_update(self, state: dict[str, Any]) -> None:
        pass

class ConnectionType(enum.Enum):
    constant = "constant"
    periodic = "periodic"
    other = "other"


class ConnectionInfo(Element):
    """Connection Info

    Parameters
    ----------
    name: str
    connection_type: ConnectionType

    connection_period: int
        The expected time between connection events (seconds) - only applicable for "periodic"
    next_connection: int
        Expected time of next connection (seconds after shutdown)
    offline_after: int
        Show as offline if disconnected for more than x secs

    """
    type = "uiConnectionInfo"

    def __init__(
        self,
        name: str = "connectionInfo",
        connection_type: ConnectionType = ConnectionType.constant,
        connection_period: int = None,
        next_connection: int = None,
        offline_after: int = None,
        allowed_misses: int = None,
        **kwargs
    ):
        super().__init__(name, None, **kwargs)
        self.name = name
        self.connection_type = connection_type
        self.connection_period = connection_period
        self.next_connection = next_connection
        self.offline_after = offline_after
        self.allowed_misses = allowed_misses

        if self.connection_type is not ConnectionType.periodic and (
            self.connection_period is not None
            or self.next_connection is not None
            or self.allowed_misses is not None
        ):
            raise RuntimeError(
                "connection_type must be periodic to set connection_period, next_connection or offline_after"
            )

    def to_dict(self):
        result = {
            "name": self.name,
            "type": self.type,
            "connectionType": self.connection_type.value,
        }

        if self.connection_period is not None:
            result['connectionPeriod'] = self.connection_period
        if self.next_connection is not None:
            result['nextConnection'] = self.next_connection
        if self.offline_after is not None:
            result['offlineAfter'] = self.offline_after
        if self.allowed_misses is not None:
            result['allowedMisses'] = self.allowed_misses

        return result


class AlertStream(Element):
    type = "uiAlertStream"

    def __init__(self, name, display_name: str = None, **kwargs):
        super().__init__(name, display_name, is_available=None, help_str=None, **kwargs)

class Multiplot(Element):
    type = "uiMultiPlot"

    def __init__(
        self,
        name: str,
        display_name: str,
        series: list[str],
        series_colours: Optional[list[Colour]] = None,
        series_active: Optional[list[bool]] = None,
        earliest_data_time: Optional[datetime] = None,
        title: Optional[str] = None,
        shared_axis: Optional[list[bool]] = None,
        step_labels: Optional[list[str]] = None,
        step_padding: Optional[list[int]] = None,
        default_zoom: Optional[str] = None,
        **kwargs
    ):
        super().__init__(name, display_name, **kwargs)

        self.series = series
        self.series_colours = series_colours
        self.series_active = series_active
        self.earliest_data_time = earliest_data_time
        self.title = title
        self.shared_axis = shared_axis
        self.step_labels = step_labels
        self.step_padding = step_padding
        self.default_zoom = default_zoom

    def to_dict(self):
        result = super().to_dict()
        result['series'] = self.series
        result['colours'] = self.series_colours

        if self.series_active is not None:
            result['activeSeries'] = self.series_active
        if self.shared_axis is not None:
            result['sharedAxis'] = self.shared_axis
        if self.step_labels is not None:
            result['stepLabels'] = self.step_labels
        if self.step_padding is not None:
            result['stepPadding'] = self.step_padding
        if self.default_zoom is not None:
            result['defaultZoom'] = self.default_zoom
        if self.title is not None:
            result['title'] = self.title

        if self.earliest_data_time is not None:
            if isinstance(self.earliest_data_time, datetime):
                result['earliestDataDate'] = int(self.earliest_data_time.timestamp())
            else:
                result['earliestDataDate'] = self.earliest_data_time

        return result


class RemoteComponent(Element):
    type = "uiRemoteComponent"

    def __init__(self, name: str, display_name: str, component_url: str, **kwargs):
        super().__init__(name, display_name, component_url=component_url)
        self.kwargs = kwargs

    def to_dict(self):
        res = super().to_dict()
        res.update(self.kwargs)
        return res


doover_ui_element = Element
doover_ui_connection_info = ConnectionInfo
doover_ui_alert_stream = AlertStream
doover_ui_multiplot = Multiplot
doover_ui_remote_component = RemoteComponent

