from view.device_menu import DeviceMenu
from view.view_parser import parse_error, parse_warning

import ipaddress as ip

R_CONFIG_MENU = ["ROUTER CONFIG MENU", "Basic config", "L3 iface config", "Redundancy config (HSRP)", "Routing config", "DHCP config", "ACL config", "Security config", "Exit"]
R_L3_IFACE_CONFIG = ["ROUTER L3 IFACE CONFIG MENU", "Modify IP address", "Add subinterface", "Add description", "Exit"]
R_DHCP_CONFIG = ["ROUTER DHCP CONFIG MENU", "Set helper address", "Exclude addresses", "Set DHCP pool", "Exit"]
R_ROUTING_CONFIG = ["ROUTER ROUTING CONFIG", "Static Routing", "OSPF", "Exit"]
R_ROUTING_OSPF_IFACE = ["ROUTER CONFIG ROUTING OSPF INTERFACES", "Config hello interval", "Config dead interval", "Add passive interfaces", "Config priority", "Config cost", "Config network point-to-point", "Exit"]
R_ROUTING_OSPF_PROCESS = ["ROUTER CONFIG ROUTING OSPF", "Config auto-cost reference-bandwidth", "Add network", "Config router id", "Redistribute gateways", "Exit"]


EXIT = -1

class RouterMenu(DeviceMenu):
    def __init__(self):
        super().__init__()
        pass

        #### PUBLIC FUNCTIONS ####

        ### ROUTER CONFIG MENU ###

    def show_router_config_menu(self) -> int:
        """
        Displays the router configuration menu and returns the selected option.

        Returns:
            int: The selected menu option.
        """
        return self.__show_menu__(R_CONFIG_MENU)

    def show_router_l3_iface_config(self, device: dict) -> int | dict:
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

    def router_iface_ip_address(self, devices: list) -> int | dict:
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
                        return info
                except ValueError:
                    print(parse_error("The IP address is not valid."))

    def router_subiface_config(self, device: dict) -> int | dict:
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

    def router_redundancy_config(self, device: dict) -> int | dict:
        """
        Prompts the user for router redundancy configuration details and returns the information as a dictionary.
        If the user exits, the function returns EXIT.

        Args:
            device (dict): Dictionary containing the current device information.

        Returns:
            int: EXIT if the user exits during input.
            dict: A dictionary containing redundancy configuration information with keys:
                - iface_list (list): List of interface names.
                - hsrp_group (int): The HSRP group number.
                - hsrp_priority (int): The HSRP priority.
                - preempt (bool): The preempt state.
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

    def show_router_dhcp_menu(self) -> int:
        """
        Show DHCP configuration menu.

        Returns:
            int: Selected menu option.
        """

        return self.__show_menu__(R_DHCP_CONFIG)

    def router_dhcp_helper_addr(self) -> int | dict:
        """
        Configure DHCP helper address.

        Returns:
            int: EXIT if the operation is exited.
            dict: Updated DHCP helper address.
                - "helper_address": ip_address  # Configured DHCP helper address.
        """

        info = dict()
        while True:
            string = input("Enter address: ")
            if string == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                try:
                    info["helper_address"] = ip.ip_address(string)
                    return info
                except ValueError:
                    print(parse_error("Invalid IP address."))

    def router_dhcp_exclude_addr(self) -> int | dict:
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
                    info["first_excluded_addr"] = ip.ip_address(string)
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
                    info["last_excluded_addr"] = ip.ip_address(string)
                    return info
                except ValueError:
                    print(parse_error("Invalid IP address."))

    def router_dhcp_pool(self, device: dict) -> int | dict:
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
                    info["pool_network"] = ip.ip_network(string)
                    break
                except Exception:
                    print(parse_error("Invalid network."))

        while True:
            string = input("Enter DNS IP (leave blank if not necessary): ")
            if string == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                try:
                    info["pool_dns_ip"] = ip.ip_address(string)
                    break
                except Exception:
                    print(parse_error("Invalid network."))
            else:
                break

        while True:
            string = input("Enter gateway IP: ")
            if string == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            if string:
                try:
                    info["pool_gateway_ip"] = ip.ip_address(string)
                    break
                except Exception:
                    print(parse_error("Invalid network."))

        return info

    def show_router_routing_menu(self) -> int:
        """
        Show routing configuration menu.

        Returns:
            int: Selected menu option.
        """

        return self.__show_menu__(R_ROUTING_CONFIG)

    def router_static_routing(self, device: dict) -> int | dict:
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
            print(device["ip_table"])
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
                    info["dest_ip"] = ip.ip_address(f"{ip}/{string}")
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
                    info["next_hop"] = ip.ip_address(string)
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

    def show_router_routing_ospf_menu(self, device: dict) -> int | dict:
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
            print(device["ip_table"])
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

    def show_router_routing_ospf_ifaces(self) -> int:
        """
        Show OSPF interface configuration menu.

        Returns:
            int: Selected menu option.
        """
        return self.__show_menu__(R_ROUTING_OSPF_IFACE)

    def router_routing_ospf_iface_hello(self, iface_list: list) -> int | list:
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

    def router_routing_ospf_iface_dead(self, iface_list: list) -> int | list:
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

    def router_routing_ospf_iface_passive(self, iface_list: list) -> int | list:
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

    def router_routing_ospf_iface_priority(self, iface_list: list) -> int | list:
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

    def router_routing_ospf_iface_cost(self, iface_list: list) -> int | list:
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

    def router_routing_ospf_iface_point_to_point(self, iface_list: list) -> int | list:
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

    def show_router_routing_ospf_process(self) -> int:
        return self.__show_menu__(R_ROUTING_OSPF_PROCESS)

    def router_routing_ospf_process_reference(self, device: dict) -> int | dict:
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

    def router_routing_ospf_process_network(self, device: dict) -> int | dict:
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
                    info['network_ip'] = string
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
                    network = ip.ip_network(f"{ip}/{string}")
                    info['network_wildcard'] = string
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

    def router_routing_ospf_process_id(self, device: dict) -> int | dict:
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

    def router_routing_ospf_process_redist(self, device: dict) -> int | dict:
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



