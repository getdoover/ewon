import json
import os

TOKEN = ""
AGENT_ID = "7369537530808909824"
ORG_ID = "7363803534221262848"
CHANNEL_NAME = "trigger"

schedule_payload = {
    "op": "on_schedule",
    "d": {
        "schedule_id": AGENT_ID,
        "organisation_id": ORG_ID,
    },
    "token": TOKEN,
}

message_create_payload = {
    "op": "on_message_create",
    "d": {
        "channel": {
            "agent_id": AGENT_ID,
            "name": CHANNEL_NAME,
        },
        "owner_id": AGENT_ID,
        "channel_name": CHANNEL_NAME,
        "author_id": ORG_ID,
        "organisation_id": ORG_ID,
        "message": {
            "id": "100000000000000000",
            "author_id": ORG_ID,
            "channel": {
                "agent_id": AGENT_ID,
                "name": CHANNEL_NAME,
            },
            "data": {
                "content": "Hello, what can you do?",
            },
            "attachments": [],
        },
    },
    "token": TOKEN,
}

# data = json.loads(event["Records"][0]["Sns"]["Message"])
# subscription_id = event["Records"][0]["EventSubscriptionArn"]

sns_payload = {
    "Records": [
        {
            "Sns": {"Message": json.dumps(message_create_payload)},
            "EventSubscriptionArn": "arn:aws:sns:ap-southeast-2:484395055539:proc-ch-7369537530808909824-trigger-onmessagecreate:5615ef2d-a456-4d62-aab7-7627d408da66",
            "EventSource": "aws:sns",
        }
    ]
}

payload = sns_payload

os.environ["DOOVER_DATA_ENDPOINT"] = "https://data.staging.udoover.com/api"

from ewon import handler

handler(payload, {})
