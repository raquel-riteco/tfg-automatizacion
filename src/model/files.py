import yaml
import json

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
        with open("config\inventory\groups.yaml", 'w') as file:
            pass 
        with open("config\inventory\hosts.yaml", 'w') as file:
            pass 
        with open("config\inventory\defaults.yaml", 'w') as file:
            pass 
        
        self.__write_yaml__("config\inventory\defaults.yaml", info)
        
    
    def load_config(self, filename: str) -> dict:
        info = self.__read_json__(filename)
        # Write hosts info into inventory/hosts.yaml
        treated_host_info = dict()
        for host in info:
            untreated_host_info = info[host]
            treated_host_info[host] = dict()
            treated_host_info[host]["hostname"] = untreated_host_info["inventory"]["hostname"]
            treated_host_info[host]["platform"] = untreated_host_info["inventory"]["platform"]
            treated_host_info[host]["groups"] = untreated_host_info["inventory"]["groups"]
            
        self.__write_yaml__("config\inventory\hosts.yaml", treated_host_info)
        # Return other info
        return info
        