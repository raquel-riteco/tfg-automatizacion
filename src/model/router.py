from typing import List
from ipaddress import IPv4Address

from model.device import Device
from model.routing_process import RoutingProcess
from model.dhcp import DHCP

class Router(Device):
    def __init__(self, hostname: str, ip_mgmt: IPv4Address, iface_mgmt: str, security: dict, interfaces: List[dict], users: List[dict] = None, banner: str = None, dhcp: dict = None, routing_process: dict = None):
        super().__init__(hostname, ip_mgmt, iface_mgmt, security, interfaces, users, banner)
        self.routing_process = RoutingProcess(routing_process["ospf_processes"], routing_process["static_routes"])
        self.dhcp = DHCP(dhcp["pools"], dhcp["helper_address"], dhcp["excluded_address"])
        
        
    def update(self, hostname: str, ip_mgmt: IPv4Address, security: dict, interfaces: List[dict], users: List[dict] = None, banner: str = None, dhcp: dict = None, routing_process: dict = None) -> None:
        """
        Updates the device attributes, including hostname, management IP, security settings, interfaces,
        users, banner, DHCP configuration, and routing process details.

        Inherits basic update functionality for hostname, management IP, security, interfaces, users,
        and banner. Additionally, initializes and sets specific configurations for DHCP and routing process.

        Args:
            hostname (str): The hostname of the device.
            ip_mgmt (IPv4Address): The management IP address of the device.
            security (dict): Security configurations, including encryption settings, console, and VTY access controls.
            interfaces (List[dict]): List of dictionaries for interface configurations.
            users (List[dict], optional): List of dictionaries with user information.
            banner (str, optional): Device banner message.
            dhcp (dict, optional): DHCP configuration details, including:
                - "pools" (List[dict]): List of DHCP address pools.
                - "helper_address" (IPv4Address): DHCP helper address.
                - "excluded_address" (List[dict]): Excluded address ranges or specific IPs.
            routing_process (dict, optional): Routing process information, including:
                - "ospf_processes" (List[dict]): List of OSPF process configurations.
                - "static_routes" (List[dict]): List of static routes.

        Returns:
            None
        """
        super().update(hostname, ip_mgmt, security, interfaces, users, banner)
        self.routing_process = RoutingProcess(routing_process["ospf_processes"], routing_process["static_routes"])
        self.dhcp = DHCP(dhcp["pools"], dhcp["helper_address"], dhcp["excluded_address"])
        
        
    def get_device_info(self) -> dict:
        device_info = super().get_device_info()
        device_info["device_type"] = "router"
        return device_info