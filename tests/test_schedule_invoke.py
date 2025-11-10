import os

os.environ["DOOVER_DATA_ENDPOINT"] = "https://data.sandbox.udoover.com/api"

from ewon import handler

payload = {
    "op": "on_schedule",
    "d": {"schedule_id": "7368786583530504192"},
    "token": "token",
}
handler(payload, {})
