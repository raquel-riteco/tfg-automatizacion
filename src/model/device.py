
from typing import List
from ipaddress import IPv4Address

from security import Security
from interface import Interface

class Device:
    def __init__(self, hostname: str, ip_mgmt: IPv4Address, users: List[dict] = None, banner: str = None):
        self.security = Security()
        self.interfaces = List[Interface]
        self.hostname = hostname
        self.ip_mgmt = ip_mgmt
        self.users = users
        self.banner = banner
        
        
       