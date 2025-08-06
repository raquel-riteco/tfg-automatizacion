from typing import List
from ipaddress import IPv4Address

from model.device import Device
from model.l3_interface import L3Interface
from model.routing_process import RoutingProcess
from model.dhcp import DHCP

class Router(Device):
    def __init__(self, hostname: str, ip_mgmt: IPv4Address, iface_mgmt: str, security: dict, interfaces: List[dict],
                 users: List[dict] = None, banner: str = None, dhcp: dict = None, routing_process: dict = None):
        super().__init__(hostname, ip_mgmt, iface_mgmt, security, users, banner)
        self.interfaces = []
        for interface in interfaces:
            new_interface = L3Interface(interface["name"], interface["is_up"], interface["description"],
                                        interface["ip_address"], interface["ospf"], interface["l3_redundancy"])
            self.interfaces.append(new_interface)
        self.routing_process = RoutingProcess(routing_process["ospf_processes"], routing_process["static_routes"])
        self.dhcp = DHCP(dhcp["pools"], dhcp["helper_address"], dhcp["excluded_address"])
        
        
    def update(self, hostname: str, security: dict, interfaces: List[dict],
               users: List[dict] = None, banner: str = None, dhcp: dict = None, routing_process: dict = None) -> None:
        """
        Updates the device attributes, including hostname, management IP, security settings, interfaces,
        users, banner, DHCP configuration, and routing process details.

        Inherits basic update functionality for hostname, management IP, security, interfaces, users,
        and banner. Additionally, initializes and sets specific configurations for DHCP and routing process.

        Args:
            hostname (str): The hostname of the device.
            security (dict): Security configurations, including encryption settings, console, and VTY access controls.
            interfaces (List[dict]): List of dictionaries for interface configurations.
            users (List[dict], optional): List of dictionaries with user information.
            banner (str, optional): Device banner message.
            interfaces (List[dict]): List of dictionaries containing interface information, where each dictionary has:
                - "name" (str): Interface name.
                - "is_up" (bool): Interface status.
                - "description" (str): Interface description.
                - "ip_address" (IPv4Address): IP address assigned to the interface.
                - "ospf" (bool): Whether OSPF is enabled.
                - "l3_redundancy" (str): Layer 3 redundancy configuration.
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
        super().update(hostname, security, users, banner)
        if interfaces:
            for new_iface in interfaces:
                for my_iface in self.interfaces:
                    if new_iface['name'] == my_iface.name:
                        my_iface.update(new_iface.get("is_up"), new_iface.get("description"),
                                        new_iface.get('ip_address'), new_iface.get('ospf'),
                                        new_iface.get('l3_redundancy'))

        if routing_process: self.routing_process.update(routing_process["ospf_processes"], routing_process["static_routes"])
        if dhcp: self.dhcp.update(dhcp["pools"], dhcp["helper_address"], dhcp["excluded_address"])
        
        
    def get_device_info(self) -> dict:
        device_info = super().get_device_info()
        device_info["device_type"] = "router"
        return device_info