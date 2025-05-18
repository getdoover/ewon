import requests
import json
from datetime import timezone, datetime

class NetbiterArgosClient:
    BASE_URL = "https://api.netbiter.net/operation/v1/rest/json"
    SYSTEM_RESOURCE_URL = f"{BASE_URL}/system"

    def __init__(self, access_key):
        self.access_key = access_key

    def get_all_systems(self):
        params = {'accesskey': self.access_key}
        response = requests.get(self.SYSTEM_RESOURCE_URL, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            self.print_error_information(response)
            return None

    def get_system_info(self, system_id):
        url = f"{self.SYSTEM_RESOURCE_URL}/{system_id}"
        params = {'accesskey': self.access_key}
        response = requests.get(url, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            self.print_error_information(response)
            return None

    def get_param_ids(self, system_id, parameter_names, mode="live"):
        """
        Fetch live parameter values for a list of parameter names from a given system.
        Returns a dictionary of {name: value}.
        """
        # Step 1: Fetch all parameters to map name -> parameterId
        param_list_url = f"{self.SYSTEM_RESOURCE_URL}/{system_id}/{mode}/config"
        params = {'accesskey': self.access_key}
        response = requests.get(param_list_url, params=params)

        if response.status_code != 200:
            self.print_error_information(response)
            return None

        all_params = response.json()
        # Filter to get only the parameters we are interested in
        all_params = [p for p in all_params if "name" in p and p["name"] in parameter_names]
        if not all_params:
            print("No matching parameters found.")
            return None
        # Create a mapping from parameter name to ID
        param_mapping = {p["name"]: p["id"] for p in all_params}
        
        return param_mapping

    def get_live_param_values(self, system_id, parameter_ids):
        """
        Fetch live parameter values for a list of parameter IDs from a given system.
        Returns a dictionary of {parameterId: value}.
        """
        param_values_url = f"{self.SYSTEM_RESOURCE_URL}/{system_id}/live"
        # Add the url parameters manually this time
        param_values_url += "?accesskey=" + self.access_key
        param_values_url += "&id=" + "&id=".join(parameter_ids)
        response = requests.get(param_values_url)

        if response.status_code != 200:
            self.print_error_information(response)
            return None

        all_params = response.json()
        # Filter to get only the parameters we are interested in
        all_params = [p for p in all_params if "id" in p and p["id"] in parameter_ids]
        
        # Create a mapping from parameter ID to value
        param_values = {p["id"]: p["value"] for p in all_params}
        
        return param_values

    def print_error_information(self, response):
        try:
            error = response.json()
            print(f"An error occurred with Argos API. Message: {error.get('message')} Code: {error.get('code')}")
        except Exception:
            print(f"An error occurred. HTTP Status: {response.status_code}. No detailed info available.")


class Netbiter:

    def __init__(self, client: NetbiterArgosClient, system_id, parameter_names):
        self.client = client
        self.system_id = system_id
        self.parameter_names = parameter_names

    def get_param_mapping(self):
        """
        Get a mapping of parameter names to IDs.
        """
        param_mapping = self.client.get_param_ids(self.system_id, self.parameter_names)
        if param_mapping is None:
            print("Failed to fetch parameter mapping.")
            return None
        self.param_map = param_mapping
        return self.param_map

    def set_clock_tz(self, tz_string):
        self._tz = tz_string

    def update(self):
        """
        Update the parameter values.
        """
        # Get the parameter mapping
        self.get_param_mapping()
        if self.param_map is None:
            print("Failed to fetch parameter mapping.")
        
    def syncdata(self, *args, **kwargs):
        return

    def create_frames(self):
        param_values = self.client.get_live_param_values(self.system_id, self.param_map.values())
        if param_values is None:
            print("Failed to fetch parameter values.")
            return None
        
        ## Create a single frame with the the current live values



class Tag:

    def __init__(self, name, id, value):
        self.name = name
        self.id = id
        self.value = value

    @property
    def tag_name(self):
        return self.name

class TagFrame:
    
    def __init__(self, tags, timestamp=None):
        self.tag_values = tags
        if timestamp:
            self.timestamp = timestamp
        else:
            self.timestamp = timezone.now()


# Example usage
if __name__ == "__main__":
    ACCESS_KEY = "your_access_key_here"
    SYSTEM_ID = "your_system_id_here"

    tag_names = ["tag1", "tag2", "tag3"]  # Replace with your actual tag names

    client = NetbiterArgosClient(ACCESS_KEY)

    # systems = client.get_all_systems()
    # print(json.dumps(systems, indent=2))

    # info = client.get_system_info(SYSTEM_ID)
    # print(json.dumps(info, indent=2))

    # param_values = client.get_param_ids(SYSTEM_ID, tag_names)
    # print(json.dumps(param_values, indent=2))

    # # Get the parameter IDs as a list
    # param_ids = list(param_values.values())
    # live_values = client.get_live_param_values(SYSTEM_ID, param_ids)
    # print(json.dumps(live_values, indent=2))

    netbiter = Netbiter(client, SYSTEM_ID, tag_names)

    netbiter.set_clock_tz("Australia/Melbourne")
    netbiter.update()
    netbiter.syncdata()
    netbiter.create_frames()
    print("Tag Frames:")
    for frame in netbiter.tag_frames:
        print(f"System ID: {frame.system_id}")
        for tag_value in frame.tag_values:
            print(f"  Tag ID: {tag_value.id}, Value: {tag_value.value}")
    