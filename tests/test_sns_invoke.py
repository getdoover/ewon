import boto3
import json

sns_client = boto3.client("sns")

topic_arn = "arn:aws:sns:ap-southeast-2:acc:proc-ch-etc."
d = {
    # "agent_id": 7368462157945913344,
    # "op": "on_message_create",
    # "d": {
    "owner_id": 7368462157945913344,
    "channel_name": "test-channel",
    "author_id": 7368462157945913344,
    "message": {
        "id": 7368462157945913344,
        "author_id": 7368462157945913344,
        "data": {"test": 1}
    }
}

custom_message_payload = {
    "agent_id": 7368462157945913344,
    "token": "token",
    "op": "on_message_create",
    "d": d,
}

try:
    response = sns_client.publish(
        TopicArn=topic_arn,
        Message=json.dumps(custom_message_payload),
    )
    print(f"Message published successfully with attributes: {response}")
except Exception as e:
    print(f"Error publishing message: {e}")
