from ipaddress import IPv4Network
from typing import Tuple

from view.device_menu import DeviceMenu
from view.view_parser import parse_error, parse_warning
import ipaddress as ip

R_CONFIG_MENU = ["ROUTER CONFIG MENU", "Basic config", "L3 iface config", "Redundancy config (HSRP)",
                 "Routing config", "DHCP config", "Exit"]
R_L3_IFACE_CONFIG = ["ROUTER L3 IFACE CONFIG MENU", "Modify IP address", "Add subinterface",
                     "Add description", "(No) Shutdown", "Exit"]
R_DHCP_CONFIG = ["ROUTER DHCP CONFIG MENU", "Set helper address", "Exclude addresses", "Set DHCP pool", "Exit"]
R_ROUTING_CONFIG = ["ROUTER ROUTING CONFIG", "Static Routing", "OSPF", "Exit"]
R_ROUTING_OSPF_IFACE = ["ROUTER CONFIG ROUTING OSPF INTERFACES", "Config hello interval",
                        "Config dead interval", "Add passive interfaces", "Config priority",
                        "Config cost", "Config network point-to-point", "Exit"]
R_ROUTING_OSPF_PROCESS = ["ROUTER CONFIG ROUTING OSPF", "Config auto-cost reference-bandwidth",
                          "Add network", "Config router id", "Redistribute gateways", "Exit"]

EXIT = -1

class RouterMenu(DeviceMenu):
    """
    Menu handler for router configuration. Supports configuration of:
    - Basic device settings
    - Layer 3 interfaces
    - Redundancy with HSRP
    - Static and OSPF routing
    - DHCP settings

    Provides interactive CLI for configuration and validates user input.
    """
    def __init__(self):
        super().__init__()

    #### PRIVATE FUNCTIONS ####

    def __show_router_config_menu__(self) -> int:
        """
        Displays the router configuration menu and returns the selected option.

        Returns:
            int: The selected menu option.
        """
        return self.__show_menu__(R_CONFIG_MENU)

    def __show_router_l3_iface_config__(self, device: dict) -> int | dict:
        """
        Show Layer 3 interface configuration for the specified device.

        Args:
            device (dict): The current device information.
                - "iface_list": list[dict]  # List of interface details, each interface is a dictionary with a "name" key.

        Returns:
            int: EXIT if the operation is exited.
            dict: Updated interface configuration.
                - "iface": str,    # Name of the selected interface.
                - "option": str    # Menu option selected.
        """

        info = dict()

        self.__show_l3_ifaces__(device)
        while True:
            found = 0
            string = input("Enter iface: ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            if string:
                for iface in device["iface_list"]:
                    if iface["name"] == string:
                        found = 1
                        break
                if not found:
                    print(parse_error("This interface does not exist."))
                else:
                    info["iface"] = string
                    break

        info["option"] = self.__show_menu__(R_L3_IFACE_CONFIG)
        return info

    def __router_iface_ip_address__(self, devices: list) -> int | dict:
        """
        Configure IP address for an interface in the network.

        Args:
            devices (list): List of devices in the network.
                - "iface_list": list[dict]  # List of interface details, each interface is a dictionary with "iface_list" as IP address key.

        Returns:
            int: EXIT if the operation is exited.
            dict: Updated IP address configuration.
                - "ip_addr": str   # Configured IP address.
        """

        info = dict()
        while True:
            string = input("Enter ip address: ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            if string:
                try:
                    ip.ip_address(string)
                    found = 0
                    for dev in devices:
                        for iface in dev["iface_list"]:
                            if iface["iface_list"] == string:
                                print(parse_error("There is another iface in the network with this IP."))
                                found = 1

                    if found == 0:
                        info["ip_addr"] = string
                        break
                except ValueError:
                    print(parse_error("The IP address is not valid."))

        while True:
            string = input("Enter mask: ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            if string:
                try:
                    ip.ip_network(f"{info['ip_addr']}/{string}", strict=False)
                    info['netmask'] = string
                    return info
                except ValueError:
                    print(parse_error("The mask is not valid."))


    def __router_subiface_config__(self, device: dict) -> int | dict:
        """
        Configure subinterface number for the specified device.

        Args:
            device (dict): The current device information.

        Returns:
            int: EXIT if the operation is exited.
            dict: Updated subinterface configuration.
                - "subiface_num": str  # Configured subinterface number.
        """

        info = dict()
        while True:
            string = input("Enter subinterface num: ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            if string:
                try:
                    num = int(string)
                    if num < 1 or num > 4096:
                        print(parse_error("Subinterface number must be between 1 and 4096, both included."))
                    else:
                        info["subiface_num"] = string
                        return info

                except ValueError:
                    print(parse_error("Subinterface number must be between 1 and 4096, both included."))

    def __router_redundancy_config__(self, device: dict) -> int | dict:
        """
        Prompts the user for router redundancy configuration details and returns the information as a dictionary.
        If the user exits, the function returns EXIT.

        Args:
            device (dict): Dictionary containing the current device information.

        Returns:
            int: EXIT if the user exits during input.
            dict: A dictionary containing redundancy configuration information with keys:
                - iface_list (list): List of interface names.
                - hsrp_virtual_ip (string): The HSRP virtual IP.
                - hsrp_group (int): The HSRP group number.
                - hsrp_priority (int): The HSRP priority.
                - hsrp_preempt (bool): The HSRP preempt state.
        """

        while True:
            self.__show_l3_ifaces__(device)
            info = dict()
            while True:
                string = input("Enter interfaces separated only by commas (ex: f0/0,f0/1,f0/2): ")
                if string.lower() == "exit":
                    print(parse_warning("Exit detected, operation not completed."))
                    return EXIT
                if string:
                    iface_list = string.split(',')
                    ok = 0
                    for iface in iface_list:
                        for x in device["iface_list"]:
                            if iface == x["name"]:
                                ok += 1
                                break
                    if ok != len(iface_list):
                        print(parse_error("One or more ifaces are not valid."))
                    else:
                        info["iface_list"] = iface_list
                        break

            while True:
                string = input("Enter group number: ")
                if string.lower() == "exit":
                    print(parse_warning("Exit detected, operation not completed."))
                    return EXIT
                if string:
                    try:
                        num = int(string)
                        if num < 1 or num > 255:
                            print(parse_error("Enter a number between 1 and 255, both included."))

                        else:
                            info["hsrp_group"] = num
                            break
                    except ValueError:
                        print(parse_error("Enter a number between 1 and 255, both included."))

            while True:
                string = input("Enter HSRP virtual IP address: ")
                if string.lower() == "exit":
                    print(parse_warning("Exit detected, operation not completed."))
                    return EXIT
                if string:
                    try:
                        ip.ip_address(string)
                        info["hsrp_virtual_ip"] = string
                        break
                    except ValueError:
                        print(parse_error("The IP address is not valid."))

            while True:
                string = input("Enter priority (default is 100): ")
                if string.lower() == "exit":
                    print(parse_warning("Exit detected, operation not completed."))
                    return EXIT
                if string:
                    try:
                        num = int(string)
                        if num < 1 or num > 255:
                            print(parse_error("Enter a number between 1 and 255, both included."))
                        else:
                            info["hsrp_priority"] = num
                            break
                    except ValueError:
                        print(parse_error("Enter a number between 1 and 255, both included."))

                else:
                    info["hsrp_priority"] = 100
                    break

            while True:
                string = input("Preempt (Y | N): ")
                match string.lower():
                    case "exit":
                        print(parse_warning("Exit detected, operation not completed."))
                        return EXIT
                    case 'y':
                        info["preempt"] = True
                        break
                    case 'n':
                        info["preempt"] = False
                        break
                    case _:
                        print(parse_error("Invalid option."))

            return info

    def __show_router_dhcp_menu__(self) -> int:
        """
        Show DHCP configuration menu.

        Returns:
            int: Selected menu option.
        """

        return self.__show_menu__(R_DHCP_CONFIG)

    def __router_dhcp_helper_addr__(self, device: dict) -> int | dict:
        """
        Configure DHCP helper address.

        Args:
            device (dict): The current device information.
                - "iface_list": list[L3_iface]  # List of DHCP pool details, each pool is a dictionary with "pool_name" as key.


        Returns:
            int: EXIT if the operation is exited.
            dict: Updated DHCP helper address information.
                - "iface" : str # Where to apply the herlper address
                - "helper_address": ip_address  # Configured DHCP helper address.
        """

        info = dict()

        while True:
            string = input("Enter iface where the helper address is applied: ")
            if string == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                found = False
                for iface in device['iface_list']:
                    if iface == string.lower():
                        found = True
                        info['iface'] = string
                        break
                if not found:
                    print(parse_error("Invalid iface, it does not exist in device."))

        while True:
            string = input("Enter address: ")
            if string == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                try:
                    ip.ip_address(string)
                    info["helper_address"] = string
                    return info
                except ValueError:
                    print(parse_error("Invalid IP address."))


    def __router_dhcp_exclude_addr__(self) -> int | dict:
        """
        Configure DHCP excluded address range.

        Returns:
            int: EXIT if the operation is exited.
            dict: Updated DHCP excluded address range.
                - "first_excluded_addr": ip_address,  # First IP address in the excluded range.
                - "last_excluded_addr": ip_address    # Last IP address in the excluded range.
        """

        info = dict()
        while True:
            string = input("Enter first address: ")
            if string == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                try:
                    ip.ip_address(string)
                    info["first_excluded_addr"] = string
                    break
                except ValueError:
                    print(parse_error("Invalid IP address."))

        while True:
            string = input("Enter last address: ")
            if string == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            if string:
                try:
                    ip.ip_address(string)
                    info["last_excluded_addr"] = string
                    return info
                except ValueError:
                    print(parse_error("Invalid IP address."))

    def __router_dhcp_pool__(self, device: dict) -> int | dict:
        """
        Configure DHCP pool for the specified device.

        Args:
            device (dict): The current device information.
                - "dhcp_pool_list": list[dict]  # List of DHCP pool details, each pool is a dictionary with "pool_name" as key.

        Returns:
            int: EXIT if the operation is exited.
            dict: Updated DHCP pool configuration.
                - "pool_name": str,       # Name of the DHCP pool.
                - "pool_network": ip_network,  # Network address of the DHCP pool.
                - "pool_dns_ip": ip_address,   # (Optional) DNS IP address for the DHCP pool.
                - "pool_gateway_ip": ip_address # Gateway IP address for the DHCP pool.
        """

        info = dict()
        while True:
            found = 0
            string = input("Enter pool name: ")
            if string == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                for pool in device["dhcp_pool_list"]:
                    if pool["pool_name"] == string:
                        print(parse_error("This name already exists."))
                        found = 1
                        break
                if not found:
                    info["pool_name"] = string
                    break

        while True:
            string = input("Enter network: ")
            if string == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                try:
                    ip.ip_network(string)
                    info["pool_network"] = string
                    break
                except Exception:
                    print(parse_error("Invalid network."))


        while True:
            string = input("Enter gateway IP: ")
            if string == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            if string:
                try:
                    ip.ip_address(string)
                    info["pool_gateway_ip"] = string
                    break
                except Exception:
                    print(parse_error("Invalid network."))

        return info

    def __show_router_routing_menu__(self) -> int:
        """
        Show routing configuration menu.

        Returns:
            int: Selected menu option.
        """

        return self.__show_menu__(R_ROUTING_CONFIG)

    def __router_static_routing__(self, device: dict) -> int | dict:
        """
        Configure static routing for the specified device.

        Args:
            device (dict): The current device information.
                - "ip_table": dict  # IP routing table for the device.

        Returns:
            int: EXIT if the operation is exited.
            dict: Updated static routing configuration.
                - "dest_ip": ip_address,        # Destination IP address with mask.
                - "next_hop": ip_address | str, # Next hop IP address or interface name.
                - "admin_distance": int         # Administrative distance for the route.
        """

        info = dict()
        while True:
            # print(device["ip_table"])
            string = input("Enter destination IP address: ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                try:
                    ip = ip.ip_address(string)
                    break
                except ValueError:
                    print(parse_error("Invalid IP address."))

        while True:
            string = input("Enter destination mask: ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                try:
                    IPv4Network(f"{ip}/{string}")
                    info["dest_ip"] = f"{ip}/{string}"
                    break
                except ValueError:
                    print(parse_error("Invalid IP mask."))

        while True:
            string = input("Enter next hop (ip address or iface): ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                try:
                    ip.ip_address(string)
                    info["next_hop"] = string
                    break
                except ValueError:
                    print(parse_error("Invalid next hop."))


        while True:
            string = input("Enter admin distance (default is 1): ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                try:
                    info["admin_distance"] = int(string)
                    break
                except ValueError:
                    print(parse_error("Invalid number, must be between 1 and 255."))
            else:
                info["admin_distance"] = 1
                break

        return info

    def __show_router_routing_ospf_menu__(self, device: dict) -> int | dict:
        """
        Show OSPF routing configuration menu for the specified device.

        Args:
            device (dict): The current device information.
                - "ip_table": dict  # IP routing table for the device.

        Returns:
            int: EXIT if the operation is exited.
            dict: Updated OSPF routing configuration.
                - "process_id": int,        # OSPF process ID.
                - "option": int,            # Option selected for OSPF configuration.
                - "iface_list": list[str]   # List of interface names for OSPF. ONLY FOR IFACE MENU OPTION
        """

        info = dict()
        while True:
            # print(device["ip_table"])
            string = input("Enter OSPF process id: ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                try:
                    num = int(string)
                    if num < 1 or num > 32:
                        print(parse_error("Invalid number, must be between 1 and 32, both included."))
                    else:
                        info["process_id"] = num
                        break
                except ValueError:
                    print(parse_error("Invalid number, must be between 1 and 32, both included."))
        while True:
            string = input("Configure interfaces (1) or routing process (2)? ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                try:
                    num = int(string)
                    match num:
                        case 1 | 2:
                            info["option"] = num
                            break
                        case _:
                            print(parse_error("Invalid number, must be 1 or 2."))
                except ValueError:
                    print(parse_error("Invalid number, must be 1 or 2."))
        if info["option"] == 1:
            while True:
                string = input("Enter interface or interfaces separated by a comma (ex: f0/0,f0/1): ")
                if string.lower() == "exit":
                    print(parse_warning("Exit detected, operation not completed."))
                    return EXIT
                if string:
                    iface_list = string.split(',')
                    ok = 0
                    for iface in iface_list:
                        for x in device["iface_list"]:
                            if iface == x["name"]:
                                ok += 1
                                break
                    if ok != len(iface_list):
                        print(parse_error("One or more ifaces are not valid."))
                    else:
                        info["iface_list"] = iface_list
                        break
        return info

    def __show_router_routing_ospf_ifaces__(self) -> int:
        """
        Show OSPF interface configuration menu.

        Returns:
            int: Selected menu option.
        """
        return self.__show_menu__(R_ROUTING_OSPF_IFACE)

    def __router_routing_ospf_iface_hello__(self, iface_list: list) -> int | list:
        """
        Configure the OSPF hello interval for each interface in the given list.

        Args:
            iface_list (list): List of interface dictionaries. Each must include:
                - 'iface_name' (str): Name of the interface.
                - 'ospf' (dict): Dictionary containing 'hello_interval'.

        Returns:
            int: EXIT if operation is cancelled.
            list: Updated list of interfaces with modified 'hello_interval'.
        """
        for iface in iface_list:
            print(f"Hello interval for {iface['iface_name']} is: {iface['ospf']['hello_interval']}")
            while True:
                string = input("Enter hello interval (default 10s): ")
                if string.lower() == "exit":
                    print(parse_warning("Exit detected, operation not completed."))
                    return EXIT
                elif string:
                    try:
                        num = int(string)
                        if num < 1 or num > 65535:
                            print(parse_error("Invalid number, must be between 1 and 65535, both included."))
                        else:
                            iface['ospf']["hello_interval"] = num
                            break
                    except ValueError:
                        print(parse_error("Invalid number, must be between 1 and 65535, both included."))
        return iface_list

    def __router_routing_ospf_iface_dead__(self, iface_list: list) -> int | list:
        """
        Configure the OSPF dead interval for each interface in the given list.

        Args:
            iface_list (list): List of interface dictionaries. Each must include:
                - 'iface_name' (str)
                - 'ospf' (dict): must contain 'dead_interval'.

        Returns:
            int: EXIT if operation is cancelled.
            list: Updated interface list with modified 'dead_interval'.
        """
        for iface in iface_list:
            print(f"Dead interval for {iface['iface_name']} is: {iface['ospf']['dead_interval']}")
            while True:
                string = input("Enter dead interval (default 40s): ")
                if string.lower() == "exit":
                    print(parse_warning("Exit detected, operation not completed."))
                    return EXIT
                elif string:
                    try:
                        num = int(string)
                        if num < 1 or num > 65535:
                            print(parse_error("Invalid number, must be between 1 and 65535, both included."))
                        else:
                            iface['ospf']["dead_interval"] = num
                            break
                    except ValueError:
                        print(parse_error("Invalid number, must be between 1 and 65535, both included."))
        return iface_list

    def __router_routing_ospf_iface_passive__(self, iface_list: list) -> int | list:
        """
        Configure whether each interface in the list is set as OSPF passive.

        Args:
            iface_list (list): List of interface dictionaries. Each must include:
                - 'iface_name' (str)
                - 'ospf' (dict): must contain 'is_passive'.

        Returns:
            int: EXIT if operation is cancelled.
            list: Updated interface list with modified 'is_passive' flags.
        """
        for iface in iface_list:
            if iface['ospf']['is_passive']:
                print(f"Interface {iface['iface_name']} is passive.")
            else:
                print(f"Interface {iface['iface_name']} is NOT passive.")
            while True:
                string = input("Set this iface as passive (y/n): ")
                if string.lower() == "exit":
                    print(parse_warning("Exit detected, operation not completed."))
                    return EXIT
                elif string:
                    if string.lower() == 'y':
                        iface['ospf']['is_passive'] = True
                        break
                    elif string.lower() == 'n':
                        iface['ospf']['is_passive'] = False
                        break
                    else:
                        print(parse_error("Invalid option."))
        return iface_list

    def __router_routing_ospf_iface_priority__(self, iface_list: list) -> int | list:
        """
        Configure the OSPF priority value for each interface in the list.

        Args:
            iface_list (list): List of interface dictionaries. Each must include:
                - 'iface_name' (str)
                - 'ospf' (dict): must contain 'priority'.

        Returns:
            int: EXIT if operation is cancelled.
            list: Updated interface list with modified 'priority' values.
        """
        for iface in iface_list:
            print(f"Priority for {iface['iface_name']} is: {iface['ospf']['priority']}")
            while True:
                string = input("Enter priority (default 40s): ")
                if string.lower() == "exit":
                    print(parse_warning("Exit detected, operation not completed."))
                    return EXIT
                elif string:
                    try:
                        num = int(string)
                        if num < 0 or num > 255:
                            print(parse_error("Invalid number, must be between 0 and 255, both included."))
                        else:
                            iface['ospf']["priority"] = num
                            break
                    except ValueError:
                        print(parse_error("Invalid number, must be between 0 and 255, both included."))
        return iface_list

    def __router_routing_ospf_iface_cost__(self, iface_list: list) -> int | list:
        """
        Configure the OSPF cost value for each interface in the list.

        Args:
            iface_list (list): List of interface dictionaries. Each must include:
                - 'iface_name' (str)
                - 'ospf' (dict): must contain 'cost'.

        Returns:
            int: EXIT if operation is cancelled.
            list: Updated interface list with modified 'cost' values.
        """
        for iface in iface_list:
            print(f"Cost for {iface['iface_name']} is: {iface['ospf']['cost']}")
            while True:
                string = input("Enter cost (default 1): ")
                if string.lower() == "exit":
                    print(parse_warning("Exit detected, operation not completed."))
                    return EXIT
                elif string:
                    try:
                        num = int(string)
                        if num < 1 or num > 65535:
                            print(parse_error("Invalid number, must be between 1 and 65535, both included."))
                        else:
                            iface['ospf']["cost"] = num
                            break
                    except ValueError:
                        print(parse_error("Invalid number, must be between 1 and 65535, both included."))
        return iface_list

    def __router_routing_ospf_iface_point_to_point__(self, iface_list: list) -> int | list:
        """
        Set OSPF point-to-point mode on interfaces.

        Args:
            iface_list (list): List of interface dictionaries. Each must include:
                - 'iface_name' (str)
                - 'ospf' (dict): must contain 'is_pint_to_point'.

        Returns:
            int: EXIT if operation is cancelled.
            list: Updated interface list with 'is_pint_to_point' flags set.
        """
        for iface in iface_list:
            if iface['ospf']['is_pint_to_point']:
                print(f"Interface {iface['iface_name']} is point-to-point.")
            else:
                print(f"Interface {iface['iface_name']} is NOT point-to-point.")
            while True:
                string = input("Set this iface as point-to-point (y/n): ")
                if string.lower() == "exit":
                    print(parse_warning("Exit detected, operation not completed."))
                    return EXIT
                elif string:
                    if string.lower() == 'y':
                        iface['ospf']['is_pint_to_point'] = True
                        break
                    elif string.lower() == 'n':
                        iface['ospf']['is_pint_to_point'] = False
                        break
                    else:
                        print(parse_error("Invalid option."))
        return iface_list

    def __show_router_routing_ospf_process__(self) -> int:
        """
        Show the OSPF process configuration menu.

        Returns:
            int: Selected menu option.
        """
        return self.__show_menu__(R_ROUTING_OSPF_PROCESS)

    def __router_routing_ospf_process_reference__(self, device: dict) -> int | dict:
        """
        Configure the OSPF auto-cost reference bandwidth for the device.

        Args:
            device (dict): Device dictionary that must contain:
                - 'ospf' (dict): with 'reference-bandwidth' key.

        Returns:
            int: EXIT if operation is cancelled.
            dict: Updated device with new reference-bandwidth.
        """
        print(f"Device OSPF auto-cost reference bandwidth is: {device['ospf']['reference-bandwidth']}")
        while True:
            string = input("Enter reference-bandwidth (default 100 Mbps): ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                try:
                    num = int(string)
                    if num < 1 or num > 4294967:
                        print(parse_error("Invalid number, must be between 1 and 4294967, both included."))
                    else:
                        device['ospf']['reference-bandwidth'] = num
                        return device
                except ValueError:
                    print(parse_error("Invalid number, must be between 1 and 4294967, both included."))

    def __router_routing_ospf_process_network__(self, device: dict) -> int | dict:
        """
        Configure a new OSPF network statement for the device.

        The user is prompted to input the network IP address, wildcard mask, and OSPF area ID.

        Args:
            device (dict): Device dictionary that must include:
                - 'ospf' (dict): with 'networks' list.

        Returns:
            int: EXIT if the operation is cancelled.
            dict: A dictionary containing:
                - 'network_ip' (str): Network IP address.
                - 'network_wildcard' (str): Wildcard mask.
                - 'network_area' (int): OSPF area ID.
        """
        print("Device OSPF networks:")
        for network in device['ospf']['networks']:
            print(f"{network}")

        info = dict()
        while True:
            string = input("Enter network ip address: ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                try:
                    ip = ip.ip_address(string)
                    break
                except ValueError:
                    print(parse_error("Invalid IP address."))

        while True:
            string = input("Enter network wildcard-mask: ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                try:
                    ip.ip_network(f"{ip}/{string}")
                    info['network_ip'] = f"{ip}/{string}"
                    break
                except ValueError:
                    print(parse_error("Invalid wildcard-mask."))

        while True:
            string = input("Enter network area id: ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                try:
                    info['network_area'] = int(string)
                    break
                except ValueError:
                    print(parse_error("Invalid wildcard-mask."))

        return info

    def __router_routing_ospf_process_id__(self, device: dict) -> int | dict:
        """
        Configure the OSPF router ID for the device.

        Args:
            device (dict): Device dictionary that must contain:
                - 'ospf' (dict): with 'router_id' key.

        Returns:
            int: EXIT if operation is cancelled.
            dict: Updated device with new router-id.
        """
        print(f"Device OSPF router-id: {device['ospf']['router_id']}")
        while True:
            string = input("Enter router-id: ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                try:
                    ip = ip.ip_address(string)
                    device['ospf']['router_id'] = string
                    break
                except ValueError:
                    print(parse_error("Invalid router-id, this must be a valid IP address."))

    def __router_routing_ospf_process_redist__(self, device: dict) -> int | dict:
        """
       Enable or disable OSPF route redistribution.

       Args:
           device (dict): Device dictionary that must contain:
               - 'ospf' (dict): with 'is_redistribute' key.

       Returns:
           int: EXIT if operation is cancelled.
           dict: Updated device with redistribution setting.
       """
        if device['ospf']['is_redistribute']:
            print(f"Device OSPF redistribution is ENABLED.")
        else:
            print(f"Device OSPF redistribution is NOT ENABLED.")
        while True:
            string = input("Set device OSPF to redistribute (y/n): ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                if string.lower() == 'y':
                    device['ospf']['is_redistribute'] = True
                    break
                elif string.lower() == 'n':
                    device['ospf']['is_redistribute'] = False
                    break
                else:
                    print(parse_error("Invalid option."))
        return device

    ### PUBLIC FUNCTIONS


    def show_router_menu(self, device: dict, devices: list, config_option: int = None) -> Tuple[dict, int] | int:
        """
        Displays the top-level router configuration menu and handles user selections.

        Dispatches to the appropriate submenus and collects user input for specific
        configuration tasks such as interface setup, routing, DHCP, etc.

        Args:
            device (dict): The device being configured.
            devices (list): List of all network devices.

        Returns:
            dict: The configuration associated data.
            int: EXIT constant if the user exits the menu.
        """

        if config_option is None:
            config_option = self.__show_router_config_menu__()

        info = dict()
        EXIT = -1
        match config_option:
            case 1:
                # Basic config
                option = self.show_device_basic_config()
                match option:
                    case 1:
                        info = self.device_dev_name(device, devices)
                    case 2:
                        info = self.device_ip_domain(device)
                    case 3:
                        info = self.device_add_user(device)
                    case 4:
                        info = self.device_remove_user(device)
                    case 5:
                        info = self.device_banner_motd(device)
                    case 6:
                        option = self.show_device_security_config()
                        match option:
                            case 1:
                                info = self.device_encrypt_passwd(device)
                            case 2:
                                info = self.device_console_access(device)
                            case 3:
                                info =  self.device_vty_access(device)
                            case 4:
                                info = self.device_enable_passwd(device)
                    case 7:
                        info = self.save_running_config()

            case 2:
                # L3 iface config
                option = self.__show_router_l3_iface_config__(device)
                match option:
                    case 1:
                        info = self.__router_iface_ip_address__(devices)
                    case 2:
                        info = self.__router_subiface_config__(device)
                    case 3:
                        info = self.device_iface_description()
                    case 4:
                        info = self.device.device_iface_shutdown()

            case 3:
                # Redundancy config (HSRP)
                info = self.__router_redundancy_config__(device)

            case 4:
                # Routing config
                option = self.__show_router_routing_menu__()
                match option:
                    case 1:
                        # Static routing
                        info = self.__router_static_routing__(device)
                    case 2:
                        # OSPF
                        info = self.__show_router_routing_ospf_menu__(device)
                        if info != EXIT:
                            if info['option'] == 1:
                                # Ifaces
                                option = self.__show_router_routing_ospf_ifaces__()
                                match option:
                                    case 1:
                                        info = self.__router_routing_ospf_iface_hello__(info['iface_list'])
                                    case 2:
                                        info = self.__router_routing_ospf_iface_dead__(info['iface_list'])
                                    case 3:
                                        info = self.__router_routing_ospf_iface_passive__(info['iface_list'])
                                    case 4:
                                        info = self.__router_routing_ospf_iface_priority__(info['iface_list'])
                                    case 5:
                                        info = self.__router_routing_ospf_iface_cost__(info['iface_list'])
                                    case 6:
                                        info = self.__router_routing_ospf_iface_point_to_point__(info['iface_list'])

                            else:
                                # Process
                                option = self.__show_router_routing_ospf_process__()
                                match option:
                                    case 1:
                                        info = self.__router_routing_ospf_process_reference__(device)
                                    case 2:
                                        info = self.__router_routing_ospf_process_network__(device)
                                    case 3:
                                        info = self.__router_routing_ospf_process_id__(device)
                                    case 4:
                                        info = self.__router_routing_ospf_process_redist__(device)

            case 5:
                # DHCP config
                option = self.__show_router_dhcp_menu__()
                match option:
                    case 1:
                        info = self.__router_dhcp_helper_addr__(device)
                    case 2:
                        info = self.__router_dhcp_exclude_addr__()
                    case 3:
                        info = self.__router_dhcp_pool__(device)
            case EXIT:
                return EXIT

        return info, config_option