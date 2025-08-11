from ipaddress import IPv4Address, IPv4Network
from typing import List

class DHCP:
    def __init__(self, pools: List[IPv4Network], helper_address: IPv4Address = None, iface_helper_address: str = None,
                 excluded_address: List[dict] = None, default_router: IPv4Address = None):
        self.helper_address = helper_address
        self.excluded_addresses = excluded_address
        self.pools = pools
        self.iface_helper_address = iface_helper_address
        self.default_router = default_router
        
        
    def update(self, pools: List[IPv4Network], helper_address: IPv4Address = None, iface_helper_address: str = None,
               excluded_address: List[dict] = None, default_router: IPv4Address = None) -> None:
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
        self.iface_helper_address = iface_helper_address
        self.default_router = default_router


    def get_info(self) -> dict:
        info = dict()
        if self.helper_address:
            info['helper_address'] = self.helper_address
        else:
            info['helper_address'] = None

        info['excluded_address'] = list()
        for excluded in info['excluded_address']:
            dictionary = dict()
            if excluded['start']:
                dictionary['start'] = excluded['start'].explode
            else:
                dictionary['start'] = None
            if excluded['end']:
                dictionary['end'] = excluded['end'].explode
            else:
                dictionary['end'] = None
            info['excluded_address'].append(dictionary)

        info['pools'] = self.pools

        if self.iface_helper_address:
            info['iface_helper_address'] = self.iface_helper_address
        else:
            info['iface_helper_address'] = None
        return info

