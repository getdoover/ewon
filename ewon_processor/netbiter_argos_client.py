import logging
from typing import Any

import requests
from datetime import datetime
from zoneinfo import ZoneInfo


log = logging.getLogger(__name__)


class Tag:
    def __init__(self, name, tag_id, value: str):
        self.name = name
        self.id = tag_id
        self.value = value

        self.description = None
        self.data_type = "Float"

        try:
            self.value = float(value)
        except ValueError:
            self.data_type = None

    @property
    def tag_name(self):
        return self.name


class TagFrame:
    def __init__(self, tags, timestamp: datetime):
        self.tag_values: list[Tag] = tags
        self.timestamp: datetime = timestamp

        self._by_name = {t.name: t for t in tags}

    def get_tag(self, tag_name):
        try:
            return self._by_name[tag_name]
        except KeyError:
            return None

    @classmethod
    def from_values(
        cls, lookup: dict[str, str], tag_values: dict[str, Any], tz: ZoneInfo = None
    ):
        tags = [
            Tag(name=lookup[tag_id], tag_id=tag_id, value=value)
            for tag_id, value in tag_values.items()
            if tag_id in lookup
        ]
        return cls(tags, datetime.now(tz=tz))


class Netbiter:
    BASE_URL = "https://api.netbiter.net/operation/v1/rest/json"
    SYSTEM_RESOURCE_URL = f"{BASE_URL}/system"

    def __init__(
        self,
        access_key: str,
        system_id: str,
        parameter_names: list[str],
        tz: ZoneInfo = None,
    ):
        self.system_id = system_id
        self.parameter_names = parameter_names
        self.tz = tz

        self.error: str | None = None
        self.param_map: dict[str, str] = {}
        self.tag_frames: list["TagFrame"] = []

        self.access_key: str = access_key
        self.session = requests.Session()

    def get(self, path, **params: Any) -> Any | None:
        url = f"{self.SYSTEM_RESOURCE_URL}/{path}"
        params["accesskey"] = self.access_key
        # print(f"GET {self.SYSTEM_RESOURCE_URL}/{path} with params: {params}")
        resp = self.session.get(url, params=params)
        if resp.status_code != 200:
            try:
                error = resp.json()
            except Exception:
                log.info(
                    f"An error occurred: {resp.url}. "
                    f"HTTP Status: {resp.status_code}. "
                    f"No detailed info available."
                )
                self.error = "No detailed info available."
            else:
                log.info(
                    f"An error occurred with Argos API. "
                    f"Message: {error.get('message')} "
                    f"Code: {error.get('code')}"
                )
                self.error = error.get("message")
            return None

        return resp.json()

    def get_all_systems(self):
        return self.get(self.SYSTEM_RESOURCE_URL)

    def get_system_info(self, system_id):
        return self.get(str(system_id))

    def get_param_ids(self, system_id, parameter_names, mode="live"):
        """
        Fetch live parameter values for a list of parameter names from a given system.
        Returns a dictionary of {name: value}.
        """
        # Step 1: Fetch all parameters to map name -> parameterId
        all_params = self.get(f"{system_id}/{mode}/config")
        if not all_params:
            return

        # Filter to get only the parameters we are interested in
        all_params = [
            p for p in all_params if "name" in p and p["name"] in parameter_names
        ]
        if not all_params:
            log.info("No matching parameters found.")
            return None
        # Create a mapping from parameter name to ID
        return {p["name"]: p["id"] for p in all_params}

    def get_live_param_values(self, system_id, parameter_ids):
        """
        Fetch live parameter values for a list of parameter IDs from a given system.
        Returns a dictionary of {parameterId: value}.
        """
        # param_values_url = f"{self.SYSTEM_RESOURCE_URL}/{system_id}/live?accesskey={self.access_key}" + "&id=" + "&id=".join(parameter_ids)
        # response = requests.get(param_values_url)
        all_params = self.get(f"{system_id}/live", id=list(parameter_ids))

        # Filter to get only the parameters we are interested in
        all_params = [p for p in all_params if "id" in p and p["id"] in parameter_ids]

        # Create a mapping from parameter ID to value
        return {p["id"]: p["value"] for p in all_params}

    def set_clock_tz(self, tz: ZoneInfo):
        """
        Set the timezone for the clock.
        """
        self.tz = tz

    def get_param_mapping(self):
        """
        Get a mapping of parameter names to IDs.
        """
        param_mapping = self.get_param_ids(self.system_id, self.parameter_names)
        if param_mapping is None:
            log.info("Failed to fetch parameter mapping.")
            return None
        self.param_map = param_mapping
        return self.param_map

    def update(self):
        """
        Update the parameter values.
        """
        # Get the parameter mapping
        self.get_param_mapping()
        if self.param_map is None:
            log.info("Failed to fetch parameter mapping.")

    def syncdata(self, *args, **kwargs):
        return

    def create_frames(self):
        param_values = self.get_live_param_values(
            self.system_id, self.param_map.values()
        )
        if param_values is None:
            log.info("Failed to fetch parameter values.")
            return None

        inverted_param_map = {v: k for k, v in self.param_map.items()}
        ## Create a single frame with the the current live values
        self.tag_frames = [
            TagFrame.from_values(inverted_param_map, param_values, self.tz)
        ]

    def get_tag(self, tag_name) -> Tag | None:
        if not self.tag_frames:
            return None

        return self.tag_frames[0].get_tag(tag_name)


# Example usage
if __name__ == "__main__":
    ACCESS_KEY = "access_key"
    SYSTEM_ID = "system_id"

    tag_names = [
        "tag_name_1",
    ]

    netbiter = Netbiter(
        ACCESS_KEY, SYSTEM_ID, tag_names, ZoneInfo("tz")
    )

    netbiter.update()
    netbiter.syncdata()
    netbiter.create_frames()

    print("Tag Frames:")
    for frame in netbiter.tag_frames:
        print(f"Frame Timestamp: {frame.timestamp}")
        print(f"{'ID':<20} | {'Name':<15} | {'Value':<10}")
        print("-" * 48)
        for tag in frame.tag_values:
            print(f"{tag.id:<20} | {tag.name:<15} | {tag.value:<10}")
