from ipaddress import IPv4Address

from model.interface import Interface


class L3Interface(Interface):
    def __init__(self, name: str, is_up: bool, description: str = None, ip_address: IPv4Address = None, ospf: dict = None, l3_redundancy: dict = None):
        super().__init__(name, is_up, description)
        self.ip_address = ip_address
        self.ospf = ospf
        self.l3_redundancy = l3_redundancy
        
        
    def update(self, is_up: bool, description: str = None, ip_address: IPv4Address = None, ospf: dict = None, l3_redundancy: dict = None) -> None:
        """
        Updates the extended interface attributes, including name, status, description, IP address,
        OSPF configuration, and Layer 3 redundancy settings.

        Inherits basic update functionality for name, status, and description, and sets additional
        attributes like IP address, OSPF configuration, and Layer 3 redundancy.

        Args:
            is_up (bool): The operational status of the interface (True if up, False if down).
            description (str, optional): A description for the interface.
            ip_address (IPv4Address, optional): The IP address assigned to the interface.
            ospf (dict, optional): OSPF (Open Shortest Path First) configuration details.
            l3_redundancy (dict, optional): Layer 3 redundancy settings, such as VRRP or HSRP configuration.

        Returns:
            None
        """
        super().update(is_up, description)
        if ip_address: self.ip_address = ip_address
        if ospf: self.ospf = ospf
        if l3_redundancy: self.l3_redundancy = l3_redundancy