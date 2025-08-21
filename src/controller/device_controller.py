from ipaddress import IPv4Address

from model.connector import Connector
from model.router import Router
from view.router_menu import RouterMenu
from view.view import View
from model.files import Files

EXIT = -1


class DeviceController:
    """
    Main controller for managing network devices.

    Responsible for creating, configuring, and retrieving information from devices.
    Handles interaction with models for device representation, configuration persistence,
    user interaction, and command execution via network connections.
    """

    def __init__(self):
        """
        Initialize the controller and its required components.
        """
        self.device = None
        self.connector = Connector()
        self.menu = None
        self.view = View()
        self.files = Files()

    def __execute_device_config__(self, device_info: dict, device_config: dict) -> None:
        """
        Execute the configuration of a device based on provided configuration data.

        Applies the configuration via Netmiko, verifies what was applied,
        updates the device model, and optionally saves the configuration.

        Args:
            device_info (dict): Dictionary with current device metadata.
            device_config (dict): Configuration to be applied. Keys may include:
                - device_name
                - save_config (bool)
                - interface, routing, DHCP, etc. details
        """
        if "device_name" in device_config:
            self.files.modify_name_in_hosts(device_info["device_name"], device_config["device_name"])
            device_name_config = dict()
            device_name_config["device_name"] = device_config["device_name"]
            self.device.update(device_name_config)

        try:
            config_lines = self.device.config(device_config)
            access_data = self.files.get_user_and_pass()
            output = self.connector.push_config_with_netmiko(
                self.device.mgmt_ip.exploded, access_data, config_lines
            )

            verify = self.device.verify_config_applied(device_config)
            print()
            if len(verify) == 0:
                self.view.print_warning("No configuration changes were made.")
            else:
                for key, status in verify.items():
                    if status:
                        self.view.print_ok(f"{key} configured correctly.")
                    else:
                        self.view.print_warning(f"{key} was not configured.")

                self.device.update(device_config)

            if device_config.get('save_config'):
                ok = self.device.save_config()
                if ok:
                    self.view.print_ok("Configuration saved to startup config.")
                else:
                    self.view.print_warning("Configuration was not saved due to an error.")

        except RuntimeError as e:
            self.view.print_error("Could not config device: " + str(e))

    def create_device(self, device_info: dict, device_config: dict = None) -> bool:
        """
        Creates a device instance based on the provided device information.

        Connects to the device to retrieve additional information and initializes a `Router` object
        if the device type is identified as "R". If a device configuration is provided,
        it applies it after creation.

        Args:
            device_info (dict): Dictionary containing device attributes:
                - device_type (str)
                - device_name (str)
                - mgmt_ip (str)
                - mgmt_iface (str)
            device_config (dict, optional): Optional configuration to apply.

        Returns:
            bool: True if the device was created successfully, False on error.
        """
        self.files.add_device_to_hosts_if_not_exists(device_info)
        try:
            connector_info = self.connector.get_device_info(device_info)

            if connector_info['device_name'] != device_info["device_name"]:
                change_device_name = self.view.ask_change_device_name(
                    connector_info['device_name'], device_info["device_name"]
                )
                if change_device_name:
                    self.files.modify_name_in_hosts(
                        device_info["device_name"], connector_info['device_name']
                    )
                    device_info["device_name"] = connector_info['device_name']

            if device_info["device_type"] == "R":
                self.menu = RouterMenu()
                self.device = Router(device_info["device_name"], IPv4Address(device_info["mgmt_ip"]),
                                     device_info["mgmt_iface"], connector_info["security"],
                                     connector_info["interfaces"], connector_info["users"],
                                     connector_info["banner_motd"], connector_info["ip_domain_lookup"],
                                     connector_info["dhcp"], connector_info["routing_process"]
                )
                if device_config and len(device_config) > 0:
                    self.__execute_device_config__(device_info, device_config)
            return True

        except RuntimeError as e:
            self.view.print_error("Device could not be created because of " + str(e))
            return False

    def configure_device(self, devices_info: list) -> None:
        """
        Opens the router configuration menu and applies configuration changes interactively.

        The configuration is shown in a loop until the user chooses to exit. Each configuration
        is validated and applied via the internal execution method.

        Args:
            devices_info (list): List of available devices in the environment.
        """
        if type(self.device) == Router:
            option = None
            while True:
                returned = self.menu.show_router_menu(self.device.get_device_info(), devices_info, option)
                if returned != EXIT:
                    info, option = returned
                    if info != -1:
                        if 'iface' in info and len(info) <= 2 and 'helper_address' not in info:
                            info = dict()
                        if len(info) > 0:
                            self.__execute_device_config__(self.device.get_device_info(), info)
                        else:
                            option = None
                else:
                    break

    def get_device_info(self) -> dict:
        """
        Retrieve current device metadata.

        Returns:
            dict: Device metadata such as name, IP, type, etc.
        """
        return self.device.get_device_info()

    def get_device_config(self) -> dict:
        """
        Retrieve the current configuration stored in the device model.

        Returns:
            dict: Device configuration.
        """
        return self.device.get_config()
