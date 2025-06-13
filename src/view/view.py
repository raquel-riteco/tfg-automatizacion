from model.subnetting import Subnetting
from view.view_parser import ViewParser
from view.router_menu import RouterMenu

from os import listdir
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv4Network
from typing import Tuple

MAIN_MENU = ["MAIN MENU", "Add device", "Remove device", "Show network", "Modify config", "Subnetting", "Exit"]


@dataclass
class Option:
    # Main menu options
    exit:           int = -1
    add_device:     int = 1
    remove_device:  int = 2
    show_network:   int = 3
    modify_config:  int = 4
    subnetting:     int = 5


class View:
    def __init__(self):
        self.parser = ViewParser()
        self.router_menu = RouterMenu()
        
        
    def __show_menu__(self, menu: list) -> int:
        """
        Displays a menu from a given list and returns the selected option as an integer.
        If the user selects the last option, the function returns EXIT.
        
        Args:
            menu (list): List containing menu options where the first element is the menu title.

        Returns:
            int: The selected menu option or EXIT if the last option is chosen.
        """
        
        option = 0
        options = Option()
        
        while(True):
            print(f"\n{menu[0]}\n")
            for i in range(1, len(menu)):
                print(f"\t{i}. {menu[i]}")
            option = input(f"\nEnter option: ")
            try:
                option = int(option)
                if (option < 1 or option > len(menu) - 1):
                    print(self.parser.parse_error("Invalid option."))
                elif (option == len(menu) - 1):
                    return options.exit
                else:
                    return option
            except ValueError:
                option = 0
                print(self.parser.parse_error("Invalid option."))
                
                
    def __add_device__(self, devices: list) -> int | dict:
        """
        Prompts the user to add a new device and returns the device information as a dictionary.
        If the user exits, the function returns EXIT.

        Args:
            devices (list): List of existing device dictionaries.

        Returns:
            int: EXIT if the user exits during input.
            dict: A dictionary containing the new device information with keys:
                - device_type (str): The type of the device (R, SW, SW-R).
                - device_name (str): The name of the device.
                - mgmt_iface (str): The management interface of the device.
                - mgmt_ip (str): The management IP address of the device.
        """
        
        info = dict()
        options = Option()
        
        while True:
            string = input("Enter device type (router: R | switch: SW | switch-router: SW-R): ")
            match string.lower():
                case "r" | "router":
                    info["device_type"] = "R"
                    break
                case "s" | "switch":
                    info["device_type"] = "SW"
                    break
                case "sw-r" | "switch-router":
                    info["device_type"] = "SW-R"
                    break
                case "exit":
                    print(self.parser.parse_warning("Exit detected, operation not completed."))
                    return options.exit
                case _:
                    print(self.parser.parse_error("Invalid option."))

        
        num = 1
        if devices != None:
            for d in devices:
                if d["device_type"] == info["device_type"]:
                    num += 1
            
        while True:
            found = 0
            string = input(f"Enter device name (default: {info['device_type']}{num}): ")
            if string.lower() == "exit":
                print(self.parser.parse_warning("Exit detected, operation not completed."))
                return options.exit
            if string:
                for d in devices:
                    if string.lower() == d["device_name"].lower():
                        print(self.parser.parse_error("A device with this name already exists."))
                        found = 1
                        break
                    
                if not found:
                    info["device_name"] = string
                    break
            else: 
                info["device_name"] = f"{info['device_type']}{num}"
                break
        
        
        string = input(f"Enter device's management iface: ")
        if string.lower() == "exit":
            print(self.parser.parse_warning("Exit detected, operation not completed."))
            return options.exit
        else: 
            info["mgmt_iface"] = string
            
        while True:
            string = input(f"Enter device's management IP address: ")
            if string.lower() == "exit":
                print(self.parser.parse_warning("Exit detected, operation not completed."))
                return options.exit
            try:
                ip = IPv4Address(string)
                info["mgmt_ip"] = ip
                break
            except:
                print(self.parser.parse_error("The IP address is not valid."))
                   
        
        return info            
                
                
    def __show_devices__(self, devices: list) -> None:
        """
        Displays a list of devices with their details.

        Args:
            devices (list): List of device dictionaries containing the following keys:
                - device_name (str): The name of the device.
                - device_type (str): The type of the device (R, SW, SW-R).
                - mgmt_iface (str): The management interface of the device.
                - mgmt_ip (str): The management IP address of the device.
        """
        
        print(f"LIST OF DEVICES -> num devices = {len(devices)}")
        print("ID\tNAME\tTYPE\tMGMT IFACE\tMGMT IP ADDRESS")
        i = 1
        for d in devices:
            print(f"{i}.\t{d['device_name']}\t{d['device_type']}\t{d['mgmt_iface']}\t{d['mgmt_ip']}")
            i += 1
    
    
    def __get_device_by__(self, devices: list, action: str) -> int | dict:
        """
        Prompts the user to select a device by ID, name, or management IP address and returns the index of the device in the list.
        If the user types 'exit', the function returns EXIT.

        Args:
            devices (list): List of device dictionaries.
            action (str): The action to be performed (e.g., "Delete", "Config").

        Returns:
            int: EXIT if the user exits during input.
            dict: A dictionary containing the new device information with keys:
                - "action_by": id, name or mgmt_ip
                - "identification": or
                    - id: int
                    - name: str
                    - mgmt_ip: IPv4Address
        """
        options = Option()
        info = dict()
        self.__show_devices__(devices)
        if len(devices) == 0:
            print(self.parser.parse_error("There are no devices."))
            return options.exit
    
        while True:
            found = -1
            string = input(f"{action} by id, name or management IP address (id | name | IP): ")
            match string.lower():
                case "id":
                    string = input("Enter id: ")
                    try:
                        found = int(string)
                        if found < 1 | found > len(devices):
                            print(self.parser.parse_error("This id does not exist."))
                        else:
                            info["action_by"] = "id"
                            info["identification"] = found
                            return info
                    except ValueError:
                        print(self.parser.parse_error("This id does not exist."))
                                                
                case "name":
                    string = input("Enter name: ")  
                    for i in range(len(devices)):
                        if devices[i]["device_name"] == string:
                            found = i
                            
                    if found == -1:
                        print(self.parser.parse_error("This name does not exist."))
                    else:
                        info["action_by"] = "name"
                        info["identification"] = string
                        return info
                    
                case "ip":
                    string = input("Enter management IP address: ")
                    try:
                        ip = IPv4Address(string)
                        for i in range(len(devices)):
                            if devices[i]["mgmt_ip"] == ip:
                                found = i
                                
                        if found == -1:
                            print(self.parser.parse_error("This management IP address does not exist."))
                        else:
                            info["action_by"] = "mgmt_ip"
                            info["identification"] = ip
                            return info
                    except: 
                        print(self.parser.parse_error("The IP address is not valid."))
                    
                case "exit":
                    print(self.parser.parse_warning("Exit detected, operation not completed."))
                    return options.exit
                
                case _:
                    print(self.parser.parse_error("Invalid option."))
    
    
    def __remove_device__(self, devices: list) -> int | dict:
        """
        Prompts the user to select a device to remove and returns the index of the device in the list.
        If the user exits, the function returns EXIT.

        Args:
            devices (list): List of existing device dictionaries.

        Returns:
            int: EXIT if the user exits during input.
            dict: A dictionary containing the new device information with keys:
                - "action_by": id, name or mgmt_ip
                - "identification": or
                    - id: int
                    - name: str
                    - mgmt_ip: IPv4Address
        """
        
        return self.__get_device_by__(devices, "Delete")
                 
    
    def __show_network__(self, devices: list) -> None:
        """
        Displays the current network, showing all connected devices.

        Args:
            devices (list): List of existing device dictionaries.
        """
        
        # TODO: For now only shows connected devices, must think about showing devices' connections
        
        self.__show_devices__(devices)             
                 
                
    def __modify_config__(self, devices: list) -> int | dict: 
        """
        Prompts the user to select a device to configure and returns the index of the device in the list.
        If the user exits, the function returns EXIT.

        Args:
            devices (list): List of existing device dictionaries.

        Returns:
            int: EXIT if the user exits during input.
            dict: A dictionary containing the new device information with keys:
                - "action_by": id, name or mgmt_ip
                - "identification": or
                    - id: int
                    - name: str
                    - mgmt_ip: IPv4Address
        """
          
        return self.__get_device_by__(devices, "Config")
    
    
    def __ask_subnetting__(self) -> int | dict:
        """
        Prompts the user for subnetting details and returns the information as a dictionary.
        If the user exits, the function returns EXIT.

        Returns:
            int: EXIT if the user exits during input.
            dict: A dictionary containing subnetting information with keys:
                - network (IPv4Network): The network address.
                - num_networks (int): The number of subnets.
                - list_num_devices (list): List of the number of devices per subnet.
        """
        
        info = dict()
        network_addr = str()
        options = Option()
        
        while True:
            string = input("Enter network: ")
            
            if string.lower() == "exit":
                print(self.parser.parse_warning("Exit detected, operation not completed."))
                return options.exit
            try:
                ip = IPv4Network(string)
                network_addr = string
                break
                
            except ValueError:
                print(self.parser.parse_error("Invalid network address."))
                
        while True:
            string = input("Enter netmask: ")
            
            if string.lower() == "exit":
                print(self.parser.parse_warning("Exit detected, operation not completed."))
                return options.exit
            try:
                if "/" in string:
                    string = string.split("/")[1]
                network = IPv4Network(f"{network_addr}/{string}", strict=False)
                info["network"] = network
                break
                
            except ValueError:
                print(self.parser.parse_error("Invalid network mask for network address."))  
            
        while True:
            string = input("Enter number of networks: ")
            
            if string.lower() == "exit":
                print(self.parser.parse_warning("Exit detected, operation not completed."))
                return options.exit
            try:
                int(string)
                info["num_networks"] = int(string)
                break
            except ValueError:
                print(self.parser.parse_error("Invalid number."))
        
        info["list_num_devices"] = list()
                
        for i in range(info["num_networks"]):
            while True:
                string = input(f"Enter number of devices in network {i + 1}: ")
                
                if string.lower() == "exit":
                    print(self.parser.parse_warning("Exit detected, operation not completed."))
                    return options.exit
                try:
                    int(string)
                    info["list_num_devices"].append(int(string))
                    break
                except ValueError:
                    print(self.parser.parse_error("Invalid number."))
                    
        return info

    def __display_subnetting__(self, info, subnets):
        """
        Displays the original subnetting input and the resulting subnets in a clean, readable format.

        Args:
            subnets (list of IPv4Network): List of generated subnets.
        """
        print("\n=== Subnetting Summary ===\n")

        base_net = info["network"]
        print(f"Base Network      : {base_net.network_address}")
        print(f"Base Netmask      : /{base_net.prefixlen}")
        print(f"Total Subnets     : {info['num_networks']}")
        print(f"Devices per Subnet: {info['list_num_devices']}\n")

        print("Generated Subnets:")
        print("------------------")
        for i, subnet in enumerate(subnets):
            hosts = list(subnet.hosts())
            first_host = hosts[0] if hosts else "N/A"
            last_host = hosts[-1] if hosts else "N/A"

            print(f"Subnet {i + 1}:")
            print(f"  Network Address : {subnet.network_address}")
            print(f"  Netmask         : {subnet.netmask} (/ {subnet.prefixlen})")
            print(f"  Broadcast Addr  : {subnet.broadcast_address}")
            print(f"  First Host      : {first_host}")
            print(f"  Last Host       : {last_host}")
            print(f"  Total Usable IPs: {subnet.num_addresses - 2}\n")

    def start_menu(self) -> Tuple[int, dict]:
        """
        Displays a menu to prompt the user for necessary configuration details, including a username, password, 
        and the option to load a hosts file. The function returns 0 if no configuration file is loaded, 
        and 1 if a configuration file is successfully loaded.

        This method handles user input for setting up default credentials and allows the user to choose 
        whether to load a configuration file from the 'db/' directory. If the file exists, the function 
        returns 1 and sets the filename in the provided `info` dictionary. If no file is loaded, it returns 0.

        Args:
            None

        Returns:
        info (dict): A dictionary to store the default username, password, and filename (if a file is loaded).
            int: 0 if no configuration file is loaded, 1 if a configuration file is successfully loaded.
        """
        info = dict()
        info["defaults"] = dict()
        path = "db/"
        string = ""
        
        # Get information for defaults file in inventory
        while not string:
            string = input("Enter username: ")
        info["defaults"]["username"] = string
        
        string = ""
        while not string:
            string = input("Enter password: ")
        info["defaults"]["password"] = string
        
        while True:
            option = input("Do you want to load a hosts file (Y | N)? ")
            if option:
                match option.lower():
                    case 'y':
                        while True:
                            # Show current files in db/
                            files = listdir(path)
                            print("Configuration files:")
                            for file in files:
                                print(f"\t- {file}")
                            # Get filename
                            string = input("Enter hosts filename: ")
                            try:
                                open(path + string, "r")
                                info["filename"] = path + string
                                return 1, info
                            except IOError:
                                # Filename not found
                                print(self.parser.parse_error(f"Could not find file {string} in {path}."))
                            
                    case 'n':
                        return 0, info   
                
    
    # If return is -1, exit program, if option is 0 do nothing, if option is number do option
    def main_menu(self, devices: list) -> Tuple[int, dict]:
        options = Option()
        # Get main menu option
        option = self.__show_menu__(MAIN_MENU)
        match option:
            case 1:
                # Add device
                info = self.__add_device__(devices)
                if info == options.exit:
                    option = 0
                                    
            case 2:
                # Remove device
                info = self.__remove_device__(devices)
                if info == options.exit:
                    option = 0

            case 3:
                self.__show_network__(devices)
            
            case 4:
                # Configure device
                info = self.__modify_config__(devices)
                if info == options.exit:
                    option = 0
            
            case 5:
                # Subnetting
                info = self.__ask_subnetting__()
                if info == options.exit:
                    option = 0
                else:
                    subnetting = Subnetting(info)
                    try:
                        result_subnetting = subnetting.generate_subnetting()
                        self.__display_subnetting__(info, result_subnetting)
                    except ValueError as e:
                        print(self.parser.parse_error(e.args[0]))
        return option, info
    
    
    def goodbye(self) -> None:
        print("\nGOODBYE!\n")
        
    def print_error(self, msg: str) -> None:
        print(self.parser.parse_error(msg))

