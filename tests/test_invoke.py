import json
import os

os.environ.update(
    **{
        "APP_KEY": "test-processor",
        "DOOVER_DATA_ENDPOINT": "https://data.sandbox.udoover.com/api",
    }
)

from ewon import handler

payload = {
    "token": "token",
    "op": "on_message_create",
    "agent_id": "7368462157945913344",
    "d": {
        "owner_id": 7368462157945913344,
        "channel_name": "test-channel",
        "author_id": 7368462157945913344,
        "message": {
            "id": 7368462157945913344,
            "author_id": 7368462157945913344,
            "data": {"test": 1},
        },
    },
}

handler({"Records": [{
    "Sns": {"Message": json.dumps(payload)},
    "EventSubscriptionArn": "arn"
}]}, {})
