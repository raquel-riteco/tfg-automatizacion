from ipaddress import IPv4Address
from typing import List

class DHCP:
    def __init__(self, pools: List[dict], helper_address: IPv4Address = None, excluded_address: List[dict] = None):
        self.helper_address = helper_address
        self.excluded_addresses = excluded_address
        self.pools = pools
        
        
    def update(self,pools: List[dict], helper_address: IPv4Address = None, excluded_address: List[dict] = None) -> None:
        """
        Updates DHCP configuration settings, including address pools, helper address, and excluded addresses.

        Sets the DHCP address pools, optional helper address, and a list of excluded addresses.

        Args:
            pools (List[dict]): List of dictionaries representing DHCP pools, where each dictionary contains:
                - Relevant attributes like pool name, range of IPs, lease duration, etc.
            helper_address (IPv4Address, optional): IP address for DHCP helper to forward DHCP requests.
            excluded_address (List[dict], optional): List of dictionaries with excluded address ranges or specific IPs.

        Returns:
            None
        """
        self.helper_address = helper_address
        self.excluded_addresses = excluded_address
        self.pools = pools