import logging
from typing import Any
from zoneinfo import ZoneInfo

import aiohttp

from datetime import datetime

from ewon_common import TagFrame, Tag, TagValue

log = logging.getLogger(__name__)


class NetbiterException(Exception):
    pass


class NetbiterAPIClient:
    BASE_URL = "https://api.netbiter.net/operation/v1/rest/json"
    SYSTEM_URL = f"{BASE_URL}/system"

    def __init__(self, access_key: str):
        self.session = None
        self.access_key = access_key

    async def setup(self):
        self.session = aiohttp.ClientSession()

    async def close(self):
        await self.session.close()

    async def _get(self, path: str, **params: Any) -> Any | None:
        url = f"{self.SYSTEM_URL}/{path}"
        params["accesskey"] = self.access_key

        async with self.session.get(url, params=params) as response:
            if response.status != 200:
                try:
                    error = await response.json()
                except Exception:
                    log.info(
                        f"An error occurred: {response.url}. "
                        f"HTTP Status: {response.status}. "
                        f"No detailed info available."
                    )
                    raise NetbiterException("No detailed info available.")
                else:
                    msg = error.get("message", "Unknown error")
                    log.info(
                        f"An error occurred with Netbiter API. "
                        f"Message: {msg} "
                        f"Code: {error.get('code')}"
                    )
                    raise NetbiterException(msg)

            return await response.json()

    async def get_system_info(self, system_id: str):
        return await self._get(str(system_id))

    async def get_param_config(self, system_id: str, mode: str = "live"):
        return await self._get(f"{system_id}/{mode}/config")

    async def get_live_params(self, system_id: str, param_ids: list):
        return await self._get(f"{system_id}/live", id=param_ids)


class NetbiterClient:
    def __init__(
        self,
        access_key: str,
        system_id: str,
        parameter_names: list[str],
        clock_tz: ZoneInfo,
    ):
        self.system_id = system_id
        self.parameter_names = parameter_names
        self.clock_tz = clock_tz

        self.client = NetbiterAPIClient(access_key)

        self.param_map: dict[str, str] = {}

        self.tags_by_id: dict[str, Tag] = {}
        self.tags_by_name: dict[str, Tag] = {}
        self.tags: list[Tag] = []

        self.tag_frames: list[TagFrame] = []

    async def setup(self):
        await self.client.setup()
        await self._fetch_param_mapping()

    async def close(self):
        await self.client.close()

    async def _fetch_param_mapping(self):
        all_params = await self.client.get_param_config(self.system_id)
        if not all_params:
            log.info("No parameters returned from Netbiter config endpoint.")
            return

        self.param_map = {
            p["name"]: p["id"]
            for p in all_params
            if "name" in p and p["name"] in self.parameter_names
        }

        if not self.param_map:
            log.info("No matching parameters found in Netbiter config.")

    async def sync_data(self, **kwargs):
        if not self.param_map:
            await self._fetch_param_mapping()
            if not self.param_map:
                log.info("Failed to fetch parameter mapping.")
                return

        param_ids = list(self.param_map.values())
        all_params = await self.client.get_live_params(self.system_id, param_ids)
        if not all_params:
            log.info("Failed to fetch live parameter values.")
            return

        param_values = {
            p["id"]: p["value"]
            for p in all_params
            if "id" in p and p["id"] in param_ids
        }

        id_to_name = {v: k for k, v in self.param_map.items()}

        now = datetime.now(tz=self.clock_tz)

        self.tags_by_id.clear()
        self.tags_by_name.clear()
        self.tags = []

        for param_id, value in param_values.items():
            name = id_to_name.get(param_id)
            if name is None:
                continue

            data_type = "Float"
            try:
                value = float(value)
            except (ValueError, TypeError):
                data_type = "String"

            tag_value = TagValue(name=name, value=value, timestamp=now)
            tag = Tag(
                tag_id=param_id,
                tag_name=name,
                data_type=data_type,
                description="",
                values=[tag_value],
            )

            self.tags_by_id[param_id] = tag
            self.tags_by_name[name] = tag
            self.tags.append(tag)

    async def create_frames(self):
        log.info(f"Creating frames for netbiter system {self.system_id}")

        self.tag_frames.clear()

        if not self.tags:
            return

        now = datetime.now(tz=self.clock_tz)
        tag_values = [tag.values[0] for tag in self.tags if tag.values]
        if tag_values:
            self.tag_frames.append(TagFrame(timestamp=now, tag_values=tag_values))

    def get_tag(self, tag_id: str):
        try:
            return self.tags_by_id[tag_id]
        except KeyError:
            return None

    def get_tag_named(self, tag_name: str):
        try:
            return self.tags_by_name[tag_name]
        except KeyError:
            return None
