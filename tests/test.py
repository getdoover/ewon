import json

x = {
    "Records": [
        {
            "EventSource": "aws:sns",
            "EventVersion": "1.0",
            "EventSubscriptionArn": "arn",
            "Sns": {
                "Type": "Notification",
                "MessageId": "id",
                "TopicArn": "arn",
                "Message": '{"op":"on_message_create","d":{"owner_id":"7368462157945913344","channel_name":"trigger","author_id":"7367427305796681728","message":{"data":{"test":2},"diff":{},"agent":"7367427305796681728","id":"7368512570845560832"}},"token":"empty","agent_id":"7368462157945913344"}',
                "Timestamp": "2025-09-02T05:18:17.582Z",
                "SignatureVersion": "1",
                "Signature": "sig",
                "SigningCertUrl": "sign",
                "Subject": None,
                "UnsubscribeUrl": "unsub-url",
                "MessageAttributes": {},
            },
        }
    ]
}

print(json.dumps(x, indent=4))

import snowflake
from datetime import datetime

x = snowflake.Snowflake.parse(7368554704042721280)
print(datetime.fromtimestamp(x.timestamp / 1000))

{
    "schedule_id": "7368786583530504192",
    "token": "token",
}
