import yaml
import json


class Files:
    """
    Handles file operations for reading/writing YAML and JSON configurations,
    managing device information, and updating Nornir inventory files.
    """

    def __init__(self):
        pass
      
    def __read_yaml__(self, filename: str) -> dict:
        """
        Reads a YAML file and returns its contents as a dictionary.

        Args:
            filename (str): The path to the YAML file to read.

        Returns:
            dict: The contents of the YAML file.
        """
        with open(filename, 'r') as file:
            return yaml.safe_load(file)
      
      
    def __write_yaml__(self, filename: str, info: dict) -> None:
        """
        Writes a dictionary to a YAML file.

        Args:
            filename (str): The path to the YAML file to write.
            info (dict): The data to write to the YAML file.

        """
        with open(filename, 'w') as file:
            yaml.safe_dump(info, file)
            
            
    def __read_json__(self, filename: str) -> dict:
        """
        Reads a JSON file and returns its contents as a dictionary.

        Args:
            filename (str): The path to the JSON file to read.

        Returns:
            dict: The contents of the JSON file.
        """
        with open(filename, 'r') as file:
            try:
                return json.load(file)
            except Exception:
                return dict()
        
        
    def __write_json__(self, filename: str, info: dict) -> None:
        """
        Writes a dictionary to a JSON file.

        Args:
            filename (str): The path to the JSON file to write.
            info (dict): The data to write to the JSON file.
        """
        with open(filename, 'w') as file:
            json.dump(info, file, indent=4)
            
        
    def save_defaults_file(self, info: dict) -> None:
        """
        Clears all contents of the inventory files and
        saves the configuration username and password into he inventory/defaults file

        Args:
            info (dict): configuration's username and password

        """
        with open("inventory/groups.yaml", 'w'): pass
        with open("inventory/hosts.yaml", 'w'): pass
        with open("inventory/defaults.yaml", 'w'): pass

        self.__write_yaml__("inventory/defaults.yaml", info)
        
    
    def load_config(self, filename: str) -> dict:
        """
        Loads configuration data from a specified JSON file, processes host information,
        and writes relevant details to an inventory file in YAML format.

        Reads the JSON file to retrieve host configurations, processes specific fields 
        (hostname, platform, and groups) to create a treated host dictionary, and saves this 
        data into an inventory file. Returns the full configuration data.

        Args:
            filename (str): Path to the JSON file containing configuration information.

        Returns:
            dict: The complete configuration data loaded from the JSON file.
        """
        info = self.__read_json__(filename)
        # Write hosts info into inventory/hosts.yaml
        treated_host_info = dict()
        groups = dict()
        for host in info:
            untreated_host_info = info[host]
            # Get info to save into hosts file in inventory
            treated_host_info[host] = dict()
            treated_host_info[host]["hostname"] = untreated_host_info["inventory"]["hostname"]
            treated_host_info[host]["platform"] = untreated_host_info["inventory"]["platform"]
            treated_host_info[host]["groups"] = untreated_host_info["inventory"]["groups"]
            for new_group in treated_host_info[host]["groups"]:
                if new_group not in groups:
                    current_group = dict()
                    current_group["group"] = new_group
                    groups[new_group] = current_group
            
        self.__write_yaml__("inventory/groups.yaml", groups)
        self.__write_yaml__("inventory/hosts.yaml", treated_host_info)
        # Return other info
        return info

    def get_user_and_pass(self) -> dict:
        """
        Retrieves default login credentials from inventory/defaults.yaml.

        Returns:
            dict: Dictionary with 'username' and 'password'.
        """
        return self.__read_yaml__("inventory/defaults.yaml")

    def modify_name_in_hosts(self, prev_name: str, new_name: str) -> None:
        """
        Renames a device entry in inventory/hosts.yaml.

        Args:
            prev_name (str): Old device name.
            new_name (str): New device name.
        """
        data = self.__read_yaml__("inventory/hosts.yaml")
        data[new_name] = data.pop(prev_name)
        self.__write_yaml__("inventory/hosts.yaml", data)

    def add_device_to_hosts_if_not_exists(self, device_info: dict) -> None:
        """
        Adds a new device to inventory/hosts.yaml if not already present.
        Also updates groups if a group is specified.

        Args:
            device_info (dict): Device data with keys like device_name, mgmt_ip, platform, group.
        """
        devices = self.__read_yaml__("inventory/hosts.yaml")
        if devices is None:
            devices = dict()

        found = False
        for device in devices:
            if device == device_info['device_name']:
                found = True
                break
        if not found:
            devices[device_info['device_name']] = dict()
            devices[device_info['device_name']]['hostname'] = device_info['mgmt_ip'].exploded
            devices[device_info['device_name']]['platform'] = device_info['platform']

            if "group" in device_info:
                devices[device_info['device_name']]['groups'] = list()
                devices[device_info['device_name']]['groups'].append(device_info['group'])
                new_group = device_info['group']
                groups = self.__read_yaml__("inventory/groups.yaml")
                if new_group not in groups:
                    current_group = dict()
                    current_group["group"] = new_group
                    groups[new_group] = current_group

                self.__write_yaml__("inventory/groups.yaml", groups)

            self.__write_yaml__("inventory/hosts.yaml", devices)


    def save_config(self, device_name: str, device_info: dict, device_config: dict, filename: str) -> None:
        """
        Saves the configuration and connection info of a device to a file in the db/ folder.

        Args:
            device_name (str): Name of the device.
            device_info (dict): Device attributes and connection data.
            device_config (dict): Configuration data.
            filename (str): Filename (without path) for saving under db/.
        """
        try:
            data = self.__read_json__(f"db/{filename}")
        except FileNotFoundError:
            data = dict()

        if device_name not in data:
            data[device_name] = dict()
            hosts_info = self.__read_yaml__("inventory/hosts.yaml")
            data[device_name]['inventory'] = hosts_info[device_name]
            if "groups" not in data[device_name]['inventory']:
                data[device_name]['inventory']['groups'] = list()

            data[device_name]['connect'] = dict()
            data[device_name]['connect']['device_type'] = device_info['device_type']
            data[device_name]['connect']['device_name'] = device_info['device_name']
            data[device_name]['connect']['mgmt_ip'] = device_info['mgmt_ip']
            data[device_name]['connect']['mgmt_iface'] = device_info['mgmt_iface']

        data[device_name]['config'] = device_config

        self.__write_json__(f"db/{filename}", data)

