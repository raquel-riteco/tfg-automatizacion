
from typing import List, cast
from ipaddress import IPv4Address

from security import Security
from l3_interface import L3Interface

class Device:
    def __init__(self, hostname: str, ip_mgmt: IPv4Address, security: dict, interfaces: List[dict], users: List[dict] = None, banner: str = None):
        self.security = Security(security["is_encrypted"], security["console_by_password"], security["vty_by_password"], security["protocols"])
        self.interfaces = List[L3Interface]
        for interface in interfaces:
            new_interface = L3Interface(interface["name"], interface["is_up"], interface["description"], interface["ip_address"], interface["ospf"], interface["l3_redundancy"])
            self.interfaces.append(new_interface)
        self.hostname = hostname
        self.ip_mgmt = ip_mgmt
        self.users = users
        self.banner = banner
        
    
    def update(self, hostname: str, interfaces: List[dict], security: dict, users: List[dict], banner: str = None) -> None:
        self.hostname = hostname
        for i in range(len(self.interfaces)):
            interface = cast(L3Interface, self.interfaces[i])
            interface.update(interfaces[i]["name"], interfaces[i]["is_up"], interfaces[i]["description"], interfaces[i]["ip_address"], interfaces[i]["ospf"], interfaces[i]["l3_redundancy"])
        self.security.update(security["is_encrypted"], security["console_by_password"], security["vty_by_password"], security["protocols"])
        self.users = users
        self.banner = banner
        