from ipaddress import IPv4Address
from typing import Any

from model.connector import Connector
from model.router import Router
from view.router_menu import RouterMenu
from view.view import Option as options
from view.view import View
from model.files import Files

class DeviceController:
    def __init__(self):
        self.device = None
        self.connector = Connector()
        self.menu = None
        self.view = View()
        self.files = Files()

    def __execute_device_config__(self, device_info: dict, device_config: dict) -> None:
        if "device_name" in device_config:
            self.files.modify_name_in_hosts(device_info["device_name"], device_config["device_name"])
            device_name_config = dict()
            device_name_config["device_name"] = device_config["device_name"]
            self.device.update(device_name_config)
        try:
            config_lines = self.device.config(device_config)
            access_data = self.files.get_user_and_pass()
            output = self.connector.push_config_with_netmiko(self.device.mgmt_ip.exploded, access_data, config_lines)

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
        if the device type is identified as "R".

        Args:
            device_info (dict): A dictionary containing the device's attributes, including:
                - "device_type" (str): Type of the device, e.g., "R".
                - "device_name" (str): Device name.
                - "mgmt_ip" (str): Management IP address.
                - "mgmt_iface" (str): Management interface.
            device_config (dict, optional)
        Returns:
            None
        """

        self.files.add_device_to_hosts_if_not_exists(device_info)
        try:
            connector_info = self.connector.get_device_info(device_info)

            if connector_info['device_name'] != device_info["device_name"]:
                change_device_name = self.view.ask_change_device_name(connector_info['device_name'],
                                                                      device_info["device_name"])
                if change_device_name:
                    self.files.modify_name_in_hosts(device_info["device_name"], connector_info['device_name'])
                    device_info["device_name"] = connector_info['device_name']

            if device_info["device_type"] == "R":
                self.menu = RouterMenu()
                self.device = Router(device_info["device_name"], IPv4Address(device_info["mgmt_ip"]),
                                     device_info["mgmt_iface"], connector_info["security"], connector_info["interfaces"],
                                     connector_info["users"], connector_info["banner_motd"],
                                     connector_info["ip_domain_lookup"], connector_info["dhcp"],
                                     connector_info["routing_process"])
                if device_config and len(device_config) > 0:
                    self.__execute_device_config__(device_info, device_config)
            return True

        except RuntimeError as e:
            self.view.print_error("Device could not be created because of " + str(e))
            return False


    def configure_device(self, devices_info: list) -> None:
        if type(self.device) == Router:
            option = None
            while True:
                returned = self.menu.show_router_menu(self.device.get_device_info(), devices_info, option)
                if returned != options.exit:
                    info, option = returned
                    if info != -1:
                        if 'iface' in info and len(info) <= 2:
                            info = dict()
                        if len(info) > 0:
                            self.__execute_device_config__(self.device.get_device_info(), info)
                        else:
                            option = None
                else:
                    break


    def get_device_info(self) -> dict:
        return self.device.get_device_info()