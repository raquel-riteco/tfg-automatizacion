from ipaddress import IPv4Address
from typing import List

class DHCP:
    def __init__(self, pools: List[dict], helper_address: IPv4Address = None, excluded_address: List[dict] = None):
        self.helper_address = helper_address
        self.excluded_addresses = excluded_address
        self.pools = pools
        
        