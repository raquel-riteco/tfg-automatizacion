from view.view_parser import parse_error, parse_warning

DEV_BASIC_CONFIG = ["DEVICE BASIC CONFIG MENU", "Device name", "IP domain lookup", "Add user", "Remove user",
                    "Banner MOTD", "Security", "Save running config", "Exit"]
DEV_SECURITY_CONFIG = ["DEVICE SECURITY CONFIG MENU", "Encrypt passwords", "Console access", "VTY access",
                       "Enable passw", "Exit"]

EXIT = -1

class DeviceMenu:

    def __init__(self) -> None:
        pass

    #### PRIVATE FUNCTIONS ####

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

        while True:
            print(f"\n{menu[0]}\n")
            for i in range(1, len(menu)):
                print(f"\t{i}. {menu[i]}")
            option = input(f"\nEnter option: ")
            try:
                option = int(option)
                if option < 1 or option > len(menu) - 1:
                    print(parse_error("Invalid option."))
                elif option == len(menu) - 1:
                    return EXIT
                else:
                    return option
            except ValueError:
                option = 0
                print(parse_error("Invalid option."))


    def __show_current_users__(self, device: dict) -> None:
        """
        Displays the current users on a given device.

        Args:
            device (dict): Dictionary containing device information, including:
                - device_name (str): The name of the device.
                - usernames (list): List of usernames on the device.
        """

        print(f"Current users in device: {device['device_name']}")
        print(f"{'USERNAME':<20} {'PRIVILEGE':<10}")
        for user in device["users"]:
            print(f"{user['username']:<20} {user['privilege']:<10}")

    #### PUBLIC FUNCTIONS ####

    ### DEVICE GENERIC CONFIG ###

    def show_device_basic_config(self) -> int:
        """
        Display the basic configuration menu for the device.

        Returns:
            int: The result of displaying the menu.
        """
        return self.__show_menu__(DEV_BASIC_CONFIG)

    def show_device_security_config(self) -> int:
        """
        Display the security configuration menu for the device.

        Returns:
            int: The result of displaying the menu.
        """
        return self.__show_menu__(DEV_SECURITY_CONFIG)

    def device_dev_name(self, device: dict, devices: list) -> int | dict:
        """
        Change the device name.

        Args:
            device (dict): The current device information, containing device information, including:
                - "device_name": str  # Current name of the device
            devices (list): List of dictionaries containing current device information
        Returns:
            int: EXIT if the operation is exited.
            dict: Updated device name.
                - "device_name": str  # New name for the device

        """

        info = dict()
        print(f"Current device name: {device['device_name']}")
        while True:
            found = 0
            string = input("Enter new device name: ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                for d in devices:
                    if string.lower() == d["device_name"].lower() and device['mgmt_ip'] != d["mgmt_ip"]:
                        print(parse_error("A device with this name already exists."))
                        found = 1
                        break

                if not found:
                    info["device_name"] = string
                    return info

    def device_ip_domain(self, device: dict) -> int | dict:
        """
        Change the IP domain lookup state of the device.

        Args:
            device (dict): The current device information.
                - "ip_domain_lookup": bool  # Current IP domain lookup state

        Returns:
            int: EXIT if the operation is exited.
            dict: Updated IP domain lookup state.
                - "ip_domain_lookup": bool  # New IP domain lookup state
        """

        info = dict()

        print(f"Current device ip domain domain lookup state: {device['ip_domain_lookup']}")
        while True:
            if device["ip_domain_lookup"]:
                string = input("Deactivate (Y | N)? ")
                match string.lower():
                    case "n":
                        return EXIT
                    case "exit":
                        print(parse_warning("Exit detected, operation not completed."))
                        return EXIT
                    case "y":
                        info["ip_domain_lookup"] = False
                        return info
                    case _:
                        print(parse_error("Invalid option."))
            else:
                string = input("Activate (Y | N)? ")
                match string.lower():
                    case "n":
                        return EXIT
                    case "exit":
                        print(parse_warning("Exit detected, operation not completed."))
                        return EXIT
                    case "y":
                        info["ip_domain_lookup"] = True
                        return info
                    case _:
                        print(parse_error("Invalid option."))

    def device_add_user(self, device: dict) -> int | dict:
        """
        Add a new user to the device.

        Args:
            device (dict): The current device information.
                - usernames": list  # List of current usernames

        Returns:
            int: EXIT if the operation is exited.
            dict: Information of the new user.
                - "username": str,   # New username
                - "password": str,   # Password for the new user
                - "privilege": int   # Privilege level of the new user
        """

        info = dict()
        self.__show_current_users__(device)
        while True:
            found = 0
            string = input("Enter new username: ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                for user in device["users"]:
                    if string.lower() == user['username'].lower():
                        print(parse_error("A user with this name already exists."))
                        found = 1
                        break

                if not found:
                    info["username"] = string
                    break

        info["password"] = input("Enter password: ")

        while True:
            found = 0
            string = input("Enter user's privilege: ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            if string:
                try:
                    info["privilege"] = int(string)
                    return info
                except ValueError:
                    print(parse_error("Privilege must be a number between 1 and 15."))

    def device_remove_user(self, device: dict) -> int | dict:
        """
        Remove an existing user from the device.

        Args:
            device (dict): The current device information.
                - "usernames": list  # List of current usernames

        Returns:
            int: EXIT if the operation is exited.
            dict: Information of the user to be removed.
                - "remove_pos": int  # Position of the user to be removed in the usernames list
        """

        info = dict()

        self.__show_current_users__(device)
        while True:
            found = 0
            string = input("Enter username to delete: ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            elif string:
                i = 0
                for user in device["users"]:
                    if string.lower() == user['username'].lower():
                        info["username_delete"] = user['username']
                        return info
                    i += 1

                if not found:
                    print(parse_error("This user does not exist."))

    def device_banner_motd(self, device: dict) -> int | dict:
        """
        Change the banner MOTD of the device.

        Args:
            device (dict): The current device information.
                - "banner": str  # Current banner MOTD

        Returns:
            int: EXIT if the operation is exited.
            dict: Updated banner MOTD.
                - "banner_motd": str  # New banner MOTD
        """

        info = dict()
        if device['banner']:
            print(f"Current banner MOTD: {device['banner']}")
        else:
            print(f"There is currently no banner MOTD")
        while True:
            string = input("Enter new banner MOTD: ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            if string:
                info["banner_motd"] = string
                return info

    def save_running_config(self) -> int | dict:
        """
        Save the running-config into the startup-config.

        Returns:
            int: EXIT if the operation is exited.
            dict: Information into if it wants to save the config.
                - "save_config": bool
        """

        info = dict()
        while True:
            string = input("Do you want to save your running config into the startup config (Y | N)? ")
            if string.lower() == 'y':
                info['save_config'] = True
                return info
            elif string.lower() == 'n' or string.lower() == 'exit':
                return EXIT


    def device_encrypt_passwd(self, device: dict) -> int | dict:
        """
        Change the password encryption state of the device.

        Args:
            device (dict): The current device information.
                - "password_encryption": bool  # Current password encryption state

        Returns:
            int: EXIT if the operation is exited.
            dict: Updated password encryption state.
                - "password_encryption": bool  # New password encryption state
        """

        info = dict()
        if device["security"]["is_encrypted"]:
            while True:
                print("Password encryption is ENABLED")
                string = input("Want to disable it (Y | N)? ")
                match string.lower():
                    case 'y':
                        info["password_encryption"] = False
                        return info
                    case 'n':
                        return EXIT
                    case 'exit':
                        print(parse_warning("Exit detected, operation not completed."))
                        return EXIT
                    case _:
                        print(parse_error("Invalid option."))
        else:
            while True:
                print("Password encryption is DISABLED")
                string = input("Want to enable it (Y | N)? ")
                match string.lower():
                    case 'y':
                        info["password_encryption"] = True
                        return info
                    case 'n':
                        return EXIT
                    case 'exit':
                        print(parse_warning("Exit detected, operation not completed."))
                        return EXIT
                    case _:
                        print(parse_error("Invalid option."))

    def device_console_access(self, device: dict) -> int | dict:
        """
        Change the console access method of the device.

        Args:
            device (dict): The current device information.
                - "console_access": str  # Current console access method ("local_database", "password")

        Returns:
            int: EXIT if the operation is exited.
            dict: Updated console access method.
                - "console_access": str  # New console access method ("local_database", "password")
                - "console_password": str # New console password
        """

        info = dict()
        match device["security"]["console_access"]:
            case "local_database":
                print("Currently, console is accessed by entering username and password stored in local database.")
                while True:
                    string = input("Want to change access to only password (Y | N)? ")
                    match string.lower():
                        case 'y':
                            info["console_access"] = "password"
                            info["console_password"] = input("Enter console password: ")
                            return info
                        case 'n':
                            return EXIT
                        case 'exit':
                            print(parse_warning("Exit detected, operation not completed."))
                            return EXIT
                        case _:
                            print(parse_error("Invalid option."))

            case "password":
                print("Currently, console is accessed by entering only a password.")
                while True:
                    string = input("Want to change access to username and password stored in local database (Y | N)? ")
                    match string.lower():
                        case 'y':
                            info["console_access"] = "local_database"
                            return info
                        case 'n':
                            return EXIT
                        case 'exit':
                            print(parse_warning("Exit detected, operation not completed."))
                            return EXIT
                        case _:
                            print(parse_error("Invalid option."))
            case _:
                print("Currently, console access is not configured.")
                while True:
                    string = input(
                        "Want to access by username and password stored in local database (1) or by only password (2)? ")
                    match string.lower():
                        case '1':
                            info["console_access"] = "local_database"
                            return info
                        case '2':
                            info["console_access"] = "password"
                            info["console_password"] = input("Enter console password: ")
                            return info
                        case 'exit':
                            print(parse_warning("Exit detected, operation not completed."))
                            return EXIT
                        case _:
                            print(parse_warning("Invalid option, enter a 1 or a 2."))

    def device_vty_access(self, device: dict) -> int | dict:
        """
        Change the VTY protocol configuration of the device.

        Args:
            device (dict): The current device information.
                - "vty_protocols": str     # Current VTY protocols ("ssh", "both")

        Returns:
            int: EXIT if the operation is exited.
            dict: Updated VTY access and/or protocol configuration.
                - "vty_protocols": str     # New VTY protocols ("ssh", "both")
        """

        info = dict()
        print("Currently, VTY lines are accessed by entering username and password stored in local database. THIS "
              "CANNOT BE CHANGED BECAUSE CONNECTION TO THE DEVICE WILL BE LOST.")

        # SSH must be configured to connect to device.
        if len(device["security"]["vty_protocols"]) == 1:
            print("Only SSH protocol configured")
            while True:
                string = input("Want to enable Telnet (Y | N)? ")
                match string.lower():
                    case 'y':
                        info["vty_protocols"] = list()
                        info["vty_protocols"].append("ssh")
                        info["vty_protocols"].append("telnet")
                        return info
                    case 'n':
                        return EXIT
                    case 'exit':
                        print(parse_warning("Exit detected, operation not completed."))
                        return EXIT
                    case _:
                        print(parse_error("Invalid option."))
        elif len(device["security"]["vty_protocols"]) > 1:
            print("Both SSH and Telnet protocols configured")
            while True:
                string = input("Want to disable Telnet (Y | N)? ")
                match string.lower():
                    case 'y':
                        info["vty_protocols"] = list()
                        info["vty_protocols"].append("ssh")
                        return info
                    case 'n':
                        return EXIT
                    case 'exit':
                        print(parse_warning("Exit detected, operation not completed."))
                        return EXIT
                    case _:
                        print(parse_error("Invalid option."))



    def device_enable_passwd(self, device: dict) -> int | dict:
        """
        Change the enable password of the device.

        Args:
            device (dict): The current device information.
                - "enable_passwd": str  # Current enable password

        Returns:
            int: EXIT if the operation is exited.
            dict: Updated enable password.
                - "enable_passwd": str  # New enable password
        """

        info = dict()
        if device["security"]["enable_by_password"]:
            print("Currently, console is accessed by entering a password.")
            while True:
                string = input("Want to update password (Y | N)? ")
                match string.lower():
                    case 'y':
                        info["enable_passwd"] = input("Enter enable password: ")
                        return info
                    case 'n':
                        return EXIT
                    case 'exit':
                        print(parse_warning("Exit detected, operation not completed."))
                        return EXIT
                    case _:
                        print(parse_error("Invalid option."))

        else:
            print("Currently, enable password is not configured.")
            while True:
                string = input("Want to set a new enable password (Y|N)? ")
                match string.lower():
                    case 'y':
                        info["enable_passwd"] = input("Enter enable password: ")
                        return info
                    case 'n':
                        return EXIT
                    case 'exit':
                        print(parse_warning("Exit detected, operation not completed."))
                        return EXIT
                    case _:
                        print(parse_error("Invalid option."))

    def device_iface_description(self, info: dict) -> int | dict:
        """
        Change the interface description.

        Returns:
            int: EXIT if the operation is exited.
            dict: Updated interface description.
                - "iface_desc": str  # New interface description
        """

        while True:
            string = input("Enter iface description: ")
            if string.lower() == "exit":
                print(parse_warning("Exit detected, operation not completed."))
                return EXIT
            if string:
                info["iface_desc"] = string
                return info


    def device_iface_shutdown(self, info: dict) -> int | dict:
        """
        Shutdown or activate an interface.

        Returns:
            int: EXIT if the operation is exited.
            dict: Updated interface description.
                - "iface_shutdown": bool
        """

        while True:
            string = input("Want to shutdown (1) or no shutdown (activate) (2) the interface (1 | 2)? ")
            match string.lower():
                case '1':
                    info["iface_shutdown"] = True
                    return info
                case '2':
                    info["iface_shutdown"] = False
                    return info
                case 'exit':
                    print(parse_warning("Exit detected, operation not completed."))
                    return EXIT
                case _:
                    print(parse_error("Invalid option."))