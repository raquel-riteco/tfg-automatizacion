from interface import Interface
from ipaddress import IPv4Address

class L3Interface(Interface):
    def __init__(self, name: str, description: str = None, ip_address: IPv4Address = None, ospf: dict = None, l3_redundancy: dict = None):
        super().__init__(name, description)
        self.ip_address = ip_address
        self.ospf = ospf
        self.l3_redundancy = l3_redundancy
        