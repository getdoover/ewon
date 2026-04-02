import csv
import ftplib
import logging
from asyncio import to_thread
from datetime import datetime
from zoneinfo import ZoneInfo

from ewon_common import TagFrame, TagValue

log = logging.getLogger(__name__)

# CSV columns: Serial Number, Date, Slave ID, Register Address, Value, Channel Index
CHANNEL_LOOKUP = {
    1: "ch4",
    2: "temperature",
    3: "main_gas_valve",
    4: "power_on",
}


def transform_value(name: str, raw: int):
    if name == "ch4":
        return round(raw * 0.003052 - 50, 2)
    elif name == "temperature":
        return round(raw * 0.039673 - 650, 2)
    else:
        return bool(raw)


class FTPClient:
    def __init__(
        self,
        server: str,
        username: str,
        password: str,
        file_name: str,
        clock_tz: ZoneInfo,
    ):
        self.server = server
        self.username = username
        self.password = password
        self.file_name = file_name
        self.clock_tz = clock_tz

        self.last_transaction_id: float | None = None
        self.tag_frames: list[TagFrame] = []

    async def setup(self):
        pass

    async def close(self):
        pass

    def _download_csv(self) -> list[dict]:
        server = ftplib.FTP(self.server)
        server.login(self.username, self.password)

        path = "/tmp/ewon_ftp.csv"
        with open(path, "wb") as fp:
            server.retrbinary(f"RETR {self.file_name}", fp.write)

        server.quit()

        with open(path, "r") as file:
            return list(csv.DictReader(file))

    async def sync_data(self, **kwargs):
        data = await to_thread(self._download_csv)

        if len(data) == 0:
            log.info("No data in FTP file")
            return

        max_ts = max(
            datetime.fromisoformat(d["Date"]) for d in data
        ).timestamp()

        if (
            self.last_transaction_id is not None
            and max_ts < self.last_transaction_id
        ):
            log.info(
                f"Skipping fetch, last transaction id: {self.last_transaction_id}, "
                f"max ts: {max_ts}"
            )
            return

        self.tag_frames.clear()

        for row in data:
            ts = datetime.fromisoformat(row["Date"])
            if self.last_transaction_id and ts.timestamp() < self.last_transaction_id:
                continue

            try:
                name = CHANNEL_LOOKUP[int(row["Channel Index"])]
            except KeyError:
                log.info(f"Skipping unknown channel index '{row['Channel Index']}'")
                continue

            raw_value = int(row["Value"])
            value = transform_value(name, raw_value)

            tag_value = TagValue(name=name, value=value, timestamp=ts)
            self.tag_frames.append(
                TagFrame(timestamp=ts, tag_values=[tag_value])
            )

        if self.tag_frames:
            self.last_transaction_id = max(
                f.timestamp.timestamp() for f in self.tag_frames
            )

    async def create_frames(self):
        # frames are already built in sync_data — one per row
        pass
