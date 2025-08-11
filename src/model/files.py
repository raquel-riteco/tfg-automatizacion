import yaml
import json
import os

class Files:
    def __init__(self):
        pass
      
    def __read_yaml__(self, filename: str) -> dict:
        """
        Reads a YAML file and returns its contents as a dictionary.

        Parameters:
            filename (str): The path to the YAML file to read.

        Returns:
            dict: The contents of the YAML file.
        """
        with open(filename, 'r') as file:
            return yaml.safe_load(file)
      
      
    def __write_yaml__(self, filename: str, info: dict) -> None:
        """
        Writes a dictionary to a YAML file.

        Parameters:
            filename (str): The path to the YAML file to write.
            info (dict): The data to write to the YAML file.

        Returns:
            None
        """
        with open(filename, 'w') as file:
            yaml.safe_dump(info, file)
            
            
    def __read_json__(self, filename: str) -> dict:
        """
        Reads a JSON file and returns its contents as a dictionary.

        Parameters:
            filename (str): The path to the JSON file to read.

        Returns:
            dict: The contents of the JSON file.
        """
        with open(filename, 'r') as file:
            return json.load(file)
        
        
    def __write_json__(self, filename: str, info: dict) -> None:
        """
        Writes a dictionary to a JSON file.

        Parameters:
            filename (str): The path to the JSON file to write.
            data (dict): The data to write to the JSON file.

        Returns:
            None
        """
        with open(filename, 'w') as file:
            json.dump(info, file, indent=4)
            
        
    def save_defaults_file(self, info: dict) -> None:
        """
        Clears all contents of the inventory files and
        saves the configuration username and password into he inventory/defaults file

        Parameters:
            info (dict): configuration's username and password

        Returns:
            None
        """
        with open("inventory/groups.yaml", 'w') as file:
            pass 
        with open("inventory/hosts.yaml", 'w') as file:
            pass 
        with open("inventory/defaults.yaml", 'w') as file:
            pass

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
        return self.__read_yaml__("inventory/defaults.yaml")

    def modify_name_in_hosts(self, prev_name: str, new_name: str) -> None:
        data = self.__read_yaml__("inventory/hosts.yaml")
        data[new_name] = data.pop(prev_name)
        self.__write_yaml__("inventory/hosts.yaml", data)

    def add_device_to_hosts_if_not_exists(self, device_info: dict) -> None:
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


    def save_subnetting(self, filename: str, subnets: list, info: dict) -> None:
        f, file_extension = os.path.splitext(filename)
        match file_extension:
            case ".txt":
                pass
            case ".csv":
                pass
            case ".json":
                pass
