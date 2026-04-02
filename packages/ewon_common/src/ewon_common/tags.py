from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


class TagValue:
    def __init__(self, name: str, value: Any, timestamp: datetime):
        self.tag_name: str = name
        self.value = value
        self.timestamp = timestamp

    @classmethod
    def from_dict(cls, data: dict, tag_name: str, data_type: str, clock_tz: ZoneInfo):
        value = data.get("value")
        if data_type == "Bool":
            value = value in [1, "1", "True", "true"]

        return cls(
            tag_name,
            value,
            datetime.fromisoformat(data.get("date")).replace(tzinfo=clock_tz),
        )

    def __repr__(self):
        return f"TagValue<value={self.value}, timestamp={self.timestamp}>"


class Tag:
    def __init__(
        self,
        tag_id: int,
        tag_name: str,
        data_type: str,
        description: str,
        values: list[TagValue],
    ):
        self.tag_id = tag_id
        self.tag_name = tag_name
        self.tag_data_type = data_type
        self.description = description

        self.values = values

    @classmethod
    def from_dict(cls, data: dict, clock_tz: ZoneInfo):
        data_type = data.get("dataType")
        tag_name = data.get("name")
        return cls(
            data.get("id"),
            tag_name,
            data_type,
            data.get("description", "").rstrip(),
            [
                TagValue.from_dict(tag, tag_name, data_type, clock_tz)
                for tag in data.get("history", [])
            ],
        )

    def pretty_print(self, verbose: bool = False):
        print(f"Tag: {self.tag_name} ({self.tag_id})")
        print(f"Description: {self.description}")
        print(f"Data Type: {self.tag_data_type}")
        print(f"History Count: {self.get_num_values()}")
        if verbose:
            for value in self.values:
                print(value)

    def get_num_values(self):
        return len(self.values)

    def __repr__(self):
        return f"Tag(tag_id={self.tag_id}, tag_name={self.tag_name}, history_count={self.get_num_values()} data_type={self.tag_data_type}, description={self.description})"


class TagFrame:
    def __init__(self, timestamp: datetime, tag_values: list[TagValue]):
        self.timestamp = timestamp
        self.tag_values = tag_values

    def __repr__(self):
        value_string = ", ".join(
            [f"{tag_val.tag_name}={tag_val.value}" for tag_val in self.tag_values]
        )
        return f"TagFrame(timestamp={self.timestamp}, {value_string})"
