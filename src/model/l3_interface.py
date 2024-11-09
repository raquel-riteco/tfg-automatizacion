from ipaddress import IPv4Address

from model.interface import Interface


class L3Interface(Interface):
    def __init__(self, name: str, is_up: bool, description: str = None, ip_address: IPv4Address = None, ospf: dict = None, l3_redundancy: dict = None):
        super().__init__(name, is_up, description)
        self.ip_address = ip_address
        self.ospf = ospf
        self.l3_redundancy = l3_redundancy
        
        
    def update(self,  name: str, is_up: bool, description: str = None, ip_address: IPv4Address = None, ospf: dict = None, l3_redundancy: dict = None) -> None:
        super().update(name, is_up, description)
        self.ip_address = ip_address
        self.ospf = ospf
        self.l3_redundancy = l3_redundancy