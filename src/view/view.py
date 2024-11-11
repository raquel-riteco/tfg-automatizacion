from view.view_parser import ViewParser
from view.router_menu import RouterMenu

from os import listdir
from dataclasses import dataclass
from ipaddress import IPv4Address
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
            string = input(f"Enter device name (default: {info["device_type"]}{num}): ")
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
                info["device_name"] = f"{info["device_type"]}{num}"
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
            print(f"{i}.\t{d["device_name"]}\t{d["device_type"]}\t{d["mgmt_iface"]}\t{d["mgmt_ip"]}")
            i += 1
    
    
    def __get_device_pos__(self, devices: list, action: str) -> int:
        """
        Prompts the user to select a device by ID, name, or management IP address and returns the index of the device in the list.
        If the user types 'exit', the function returns EXIT.

        Args:
            devices (list): List of device dictionaries.
            action (str): The action to be performed (e.g., "Delete", "Config").

        Returns:
            int: The index of the selected device in the list or EXIT if no device is found or the user exits.
        """
        options = Option()
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
                    for i in range(len(devices)):
                        if devices[i]["device_id"] == string:
                            found = i
                            
                    if found == -1:
                        print(self.parser.parse_error("This id does not exist."))
                    else:
                        return found
                                                
                case "name":
                    string = input("Enter name: ")  
                    for i in range(len(devices)):
                        if devices[i]["device_name"] == string:
                            found = i
                            
                    if found == -1:
                        print(self.parser.parse_error("This name does not exist."))
                    else:
                        return found
                    
                case "ip":
                    string = input("Enter management IP address: ")
                    for i in range(len(devices)):
                        if devices[i]["mgmt_ip"] == string:
                            found = i
                            
                    if found == -1:
                        print(self.parser.parse_error("This management IP address does not exist."))
                    else:
                        return found 
                    
                case "exit":
                    print(self.parser.parse_warning("Exit detected, operation not completed."))
                    return options.exit
                
                case _:
                    print(self.parser.parse_error("Invalid option."))
    
    
    def __remove_device__(self, devices: list) -> int:
        """
        Prompts the user to select a device to remove and returns the index of the device in the list.
        If the user exits, the function returns EXIT.

        Args:
            devices (list): List of existing device dictionaries.

        Returns:
            int: The index of the device to be removed or EXIT if the user exits.
        """
        
        return self.__get_device_pos__(devices, "Delete")
                 
                
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
                pass
            
            case 4:
                pass
            
            case 5:
                pass
            
        return option, info
    
    
    def goodbye(self) -> None:
        print("\nGOODBYE!\n")
        
        