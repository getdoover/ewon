import asyncio
import zoneinfo
from datetime import timezone

from src.ewon.ewon_client import EwonClient


async def main():
    token = "token"
    developer_id = "dev-id"
    clock_tz = zoneinfo.ZoneInfo("Australia/Sydney")

    ewon_id = 0000000
    ewon_name = "LaTrobe"

    device = EwonClient(token, developer_id, clock_tz, ewon_id, ewon_name)
    await device.setup()

    # print(await device.client.get_status())
    # print(await device.client.get_ewons())

    # print(device.tags)
    # device.pretty_print()
    # for tag in device.tags:
    #     tag.pretty_print()
    #     print("")

    await device.sync_data(create_transaction=False)
    print(device.tags)

    print(device.get_tag_named("CH4"))

    await device.create_frames()
    print(device.tag_frames)
    print(len(device.tag_frames))

    await device.close()

    # print(client.syncdata())

    # ## write syncdata data to a file
    # with open("syncdata.json", "w") as f:
    #     data = client.syncdata()
    #     f.write(json.dumps(data, indent=4))
    #     # print(data)

if __name__ == "__main__":
    asyncio.run(main())
