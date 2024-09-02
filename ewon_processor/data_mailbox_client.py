#!/usr/bin/env python3

from pydatamailbox import (
    DataMailbox,
    # DataMailboxArgsError,
    # DataMailboxBaseException,
    # M2Web,
)

from typing import Any, Union, Callable, overload, Literal, Optional, TypeVar, List
from datetime import datetime, timezone
from dateutil import parser, tz
import json



def time_to_iso_string(time: Union[datetime, int, str]) -> str:
    if time:
        if isinstance(time, datetime):
            time = time.isoformat()
        elif isinstance(time, str):
            try:
                time = parser.isoparse(time).isoformat()
            except ValueError:
                raise ValueError("time must be either a datetime, epoch seconds or ISO formatted string")
        elif isinstance(time, (int, float)):
            time = datetime.fromtimestamp(time).isoformat()
        else:
            raise ValueError("time must be either a datetime, epoch seconds or ISO formatted string")
    return time



class DataMailboxClient:

    def __init__(self, token: str, devid: str = None, account: str = None):
        self.token = token
        self.devid = devid
        self.account = account

        self._dm = None

        self.setup()

    def setup(self):
        self._dm = DataMailbox(token=self.token, devid=self.devid, account=self.account)
        self._dm.data.pop("t2maccount", None)

    def getstatus(self):
        return self._dm.getstatus()

    def getewons(self):
        return self._dm.getewons()

    def getewon(self, ewon_id: int, ewon_name: str = None):
        return self._dm.getewon(ewon_id, ewon_name)

    def getdata(self, ewon_id: int, tag_id: int, start: Union[str, int, datetime], end: Union[str, int, datetime], limit: int):
        from_ts = time_to_iso_string(start)
        to_ts = time_to_iso_string(end)
        return self._dm.getdata(ewon_id, tag_id, from_ts, to_ts, limit)

    def syncdata(self, last_transaction_id=None, create_transaction=True, ewon_ids=None):
        return self._dm.syncdata(last_transaction_id, create_transaction, ewon_ids)
    
    def iterate_syncdata(self, last_transaction_id=None, ewon_ids=None):
        return self._dm.iterate_syncdata(last_transaction_id, ewon_ids)


class Ewon:

    def __init__(self, client: DataMailboxClient, ewon_id: int, ewon_name: Optional[str] = None, last_transaction_id: Optional[int] = None):
        self.client = client
        self.ewon_id = ewon_id
        self.ewon_name = ewon_name

        self.clock_tz = timezone.utc

        self.last_transaction_id = last_transaction_id
        self.tags = [] # List[Tag]
        self.tag_frames = [] # List[TagFrame]

    def set_clock_tz(self, tz: Union[str, timezone]):
        if isinstance(tz, str):
            tz = timezone(tz)
        print(f"Setting clock timezone to {tz}")
        self.clock_tz = tz

    def update(self):
        ewon_data = self.client.getewon(self.ewon_id, self.ewon_name)
        self.from_json(ewon_data)

    def get_tag(self, tag_name: Optional[str] = None, tag_id: Optional[int] = None):
        if tag_name:
            for tag in self.tags:
                if tag.tag_name == tag_name:
                    return tag
        elif tag_id:
            for tag in self.tags:
                if tag.tag_id == tag_id:
                    return tag
        return None


    ## A function that creates frames from the tag values
    def create_frames(self):
        if self.tags.__len__() == 0:
            self.update()
        
        for tag in self.tags:
            for value in tag.values:
                frame = None
                for f in self.tag_frames:
                    if f.tag_ts_matches(value):
                        frame = f
                        break
                if frame is None:
                    print(f"Creating new frame for {value}, with timestamp {value.timestamp}")
                    frame = TagFrame(ewon=self, timestamp=value.timestamp, tag_values=[value])
                else:
                    frame.add_tag_value(value)

                if frame not in self.tag_frames:
                    self.tag_frames.append(frame)

    def pretty_print(self, verbose: bool = False):
        print(f"Ewon: {self.ewon_name} ({self.ewon_id})")
        print(f"Last Transaction ID: {self.last_transaction_id}")
        print(f"Tags: {self.tags.__len__()}")
        print(f"Frames {self.tag_frames.__len__()}:")
        if verbose:
            for f in self.tag_frames:
                print(f)

    def syncdata(self, create_transaction: Optional[bool] = None):

        if self.last_transaction_id is None and create_transaction is None:
            create_transaction = True
        else:
            create_transaction = create_transaction or False

        data = self.client.syncdata(last_transaction_id=self.last_transaction_id, create_transaction=create_transaction, ewon_ids=[self.ewon_id])
        
        self.last_transaction_id = data.get("transactionId")

        ## get the ewon data
        ewons = data.get("ewons")
        if ewons and ewons.__len__() > 0:
            ewon_data = ewons[0]
            self.from_json(ewon_data)

            return self

        return None

    def from_json(self, data: dict):
        self.json_data = data

        self.ewon_id = data.get("id")
        self.ewon_name = data.get("name")

        tags = data.get("tags")
        if tags:
            self.tags = [Tag(ewon=self, data=tag, clock_tz=self.clock_tz) for tag in tags]


class Tag:

    def __init__(self, 
                ewon: Ewon,
                tag_id: Optional[int] = None,
                tag_name: Optional[str] = None,
                data_type: Optional[str] = None,
                description: Optional[str] = None,
                data: Optional[dict] = None,
                clock_tz: Optional[timezone] = None,
            ):
        self.ewon = ewon
        
        self.tag_id = tag_id
        self.tag_name = tag_name
        self.tag_data_type = data_type
        self.description = description
        
        self.clock_tz = clock_tz

        self.values = [] # List[TagValue]

        if data:
            self.from_json(data)

    def from_json(self, data: dict):
        self.tag_id = data.get("id")
        self.tag_name = data.get("name")
        self.tag_data_type = data.get("dataType")
        self.description = data.get("description")

        if self.description:
            self.description = self.description.rstrip()

        history = data.get("history")
        if history:
            self.values = [TagValue(tag=self, data=tag, clock_tz=self.clock_tz) for tag in history]

    def pretty_print(self, verbose: bool = False):
        print(f"Tag: {self.tag_name} ({self.tag_id})")
        print(f"Description: {self.description}")
        print(f"Data Type: {self.tag_data_type}")
        print(f"History Count: {self.get_num_values()}")
        if verbose:
            for value in self.values:
                print(value)

    def get_num_values(self):
        return self.values.__len__()

    def __repr__(self):
        return f"Tag(tag_id={self.tag_id}, tag_name={self.tag_name}, history_count={self.get_num_values()} data_type={self.tag_data_type}, description={self.description})"


class TagValue:

    def __init__(self, tag: Tag, data: Optional[dict] = None, clock_tz: Optional[timezone] = None):
        self.tag = tag

        self.value = None
        self.timestamp = None

        self.clock_tz = clock_tz

        if data:
            self.from_json(data)

    def from_json(self, data: dict):

        self.value = data.get("value")
        if self.tag.tag_data_type == "Bool":
            self.value = data.get("value") in [1, "1", "True", "true"]

        self.timestamp = data.get("date")
        self.timestamp = parser.isoparse(self.timestamp)

        self.timestamp = self.timestamp.replace(tzinfo=self.clock_tz)

    @property
    def tag_name(self):
        return self.tag.tag_name

    def __repr__(self):
        return f"TagValue(tag_name={self.tag.tag_name}, value={self.value}, timestamp={self.timestamp})"


class TagFrame:

    def __init__(self, ewon: Ewon, timestamp: datetime, tag_values: List[TagValue]):
        self.ewon = ewon

        self.timestamp = timestamp
        self.tag_values = tag_values

    def tag_ts_matches(self, tag_value: TagValue):
        ## if timestamp is equal, or within 5 mins
        within_mins = 5

        if self.timestamp == tag_value.timestamp:
            return True
        elif abs((self.timestamp - tag_value.timestamp).total_seconds()) < (within_mins*60):
            return True
        return False
    
    def add_tag_value(self, tag_value: TagValue):
        self.tag_values.insert(0, tag_value)

    def __repr__(self):
        value_string = ", ".join([f"{tag_val.tag.tag_name}={tag_val.value}" for tag_val in self.tag_values])
        return f"TagFrame(timestamp={self.timestamp}, {value_string})"


if __name__ == "__main__":

    token = "<>"
    developer_id = "<>"

    ewon_id = 0000000

    client = DataMailboxClient(token=token, devid=developer_id)
    # print(client.getstatus())
    # print(client.getewons())


    test_ewon = Ewon(client=client, ewon_id=ewon_id)
    
    # test_ewon.update()
    # print(test_ewon.tags)

    test_ewon.syncdata()
    print(test_ewon.tags)

    test_ewon.get_tag("CH4").pretty_print()

    test_ewon.create_frames()
    test_ewon.pretty_print()

    # print(client.syncdata())

    # ## write syncdata data to a file
    # with open("syncdata.json", "w") as f:
    #     data = client.syncdata()
    #     f.write(json.dumps(data, indent=4))
    #     # print(data)
