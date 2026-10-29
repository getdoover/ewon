import csv
import html
import io
import logging
import re

import aiohttp

log = logging.getLogger(__name__)


class M2WebException(Exception):
    pass


class M2WebClient:
    """Talk2M M2Web: requests proxied through Talk2M to the Ewon's own web server.

    Unlike DataMailbox this reaches the live device, so the Ewon has to be
    online to Talk2M. It needs a real Talk2M user: API tokens are rejected
    because they can't be used for remote access to devices.
    """

    BASE_URL = "https://m2web.talk2m.com/t2mapi/get/"

    def __init__(
        self,
        account: str,
        username: str,
        password: str,
        developer_id: str,
        ewon_name: str,
        device_username: str,
        device_password: str,
        timeout: float = 15,
    ):
        self.ewon_name = ewon_name
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None
        self.auth = {
            "t2maccount": account,
            "t2musername": username,
            "t2mpassword": password,
            "t2mdeveloperid": developer_id,
            "t2mdeviceusername": device_username,
            "t2mdevicepassword": device_password,
        }

    async def setup(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)

    async def close(self):
        if self.session:
            await self.session.close()

    async def _request(self, path: str, data: dict) -> str:
        url = f"{self.BASE_URL}{self.ewon_name}/{path}"
        async with self.session.post(url, data={**data, **self.auth}) as response:
            body = await response.text(encoding="latin-1")
            if response.status != 200:
                raise M2WebException(
                    f"M2Web {path} failed ({response.status}): {body[:200]}"
                )
            return body

    async def write_tags(self, values: dict[str, float | int]):
        data = {}
        for i, (name, value) in enumerate(values.items(), start=1):
            data[f"TagName{i}"] = name
            data[f"TagValue{i}"] = str(value)

        # The Ewon answers 200 either way, with a "Done" or "ERROR: ..." HTML page.
        body = await self._request("rcgi.bin/UpdateTagForm", data)
        text = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", body)).split())
        if not text.endswith("Done"):
            raise M2WebException(
                text.removeprefix("Error ").strip() or "Ewon rejected the write"
            )
        log.info(f"UpdateTagForm {values}: done")

    async def read_tags(self) -> dict[str, str]:
        """Instantaneous values of every tag, keyed by Ewon tag name."""
        body = await self._request("rcgi.bin/ParamForm", {"AST_Param": "$dtIV$ftT"})
        rows = csv.DictReader(io.StringIO(body.strip()), delimiter=";")
        return {row["TagName"]: row["Value"] for row in rows if row.get("TagName")}
