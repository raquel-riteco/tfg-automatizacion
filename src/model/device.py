
from typing import List, cast
from ipaddress import IPv4Address

from model.security import Security
from model.l3_interface import L3Interface

class Device:
    def __init__(self, hostname: str, mgmt_ip: IPv4Address, mgmt_iface: str, security: dict, interfaces: List[dict], users: List[dict] = None, banner: str = None):
        self.security = Security(security["is_encrypted"], security["console_by_password"], security["vty_by_password"], security["protocols"])
        self.interfaces = List[L3Interface]
        for interface in interfaces:
            new_interface = L3Interface(interface["name"], interface["is_up"], interface["description"], interface["ip_address"], interface["ospf"], interface["l3_redundancy"])
            self.interfaces.append(new_interface)
        self.hostname = hostname
        self.mgmt_ip = mgmt_ip
        self.mgmt_iface = mgmt_iface
        self.users = users
        self.banner = banner
        
    
    def update(self, hostname: str, interfaces: List[dict], security: dict, users: List[dict], banner: str = None) -> None:
        """
        Updates device settings, including hostname, interfaces, security configurations, users, and banner.

        Sets the hostname, updates each interface with specified attributes, adjusts security settings, 
        and updates the list of users and optional device banner.

        Args:
            hostname (str): The hostname of the device.
            interfaces (List[dict]): List of dictionaries containing interface information, where each dictionary has:
                - "name" (str): Interface name.
                - "is_up" (bool): Interface status.
                - "description" (str): Interface description.
                - "ip_address" (IPv4Address): IP address assigned to the interface.
                - "ospf" (bool): Whether OSPF is enabled.
                - "l3_redundancy" (str): Layer 3 redundancy configuration.
            security (dict): Dictionary containing security settings, including:
                - "is_encrypted" (bool): Whether security is encrypted.
                - "console_by_password" (bool): Console access secured by password.
                - "vty_by_password" (bool): VTY (Virtual Teletype) access secured by password.
                - "protocols" (list): List of enabled security protocols.
            users (List[dict]): List of dictionaries with user information.
            banner (str, optional): Device banner message.

        Returns:
            None
        """
        self.hostname = hostname
        for i in range(len(self.interfaces)):
            interface = cast(L3Interface, self.interfaces[i])
            interface.update(interfaces[i]["name"], interfaces[i]["is_up"], interfaces[i]["description"], interfaces[i]["ip_address"], interfaces[i]["ospf"], interfaces[i]["l3_redundancy"])
        self.security.update(security["is_encrypted"], security["console_by_password"], security["vty_by_password"], security["protocols"])
        self.users = users
        self.banner = banner
        
        
    def get_device_info(self) -> dict:
        device_info = dict()
        device_info["device_name"] = self.hostname
        device_info["mgmt_iface"] = self.mgmt_ip
        device_info["mgmt_ip"] = self.mgmt_iface