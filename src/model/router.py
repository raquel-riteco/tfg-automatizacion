from typing import List
from ipaddress import IPv4Address

from model.device import Device
from model.routing_process import RoutingProcess
from model.dhcp import DHCP

class Router(Device):
    def __init__(self, hostname: str, ip_mgmt: IPv4Address, iface_mgmt: str, security: dict, interfaces: List[dict], users: List[dict] = None, banner: str = None, dhcp: dict = None, routing_process: dict = None):
        super().__init__(hostname, ip_mgmt, iface_mgmt, security, interfaces, users, banner)
        self.routing_process = RoutingProcess(routing_process["ospf_processes"], routing_process["static_routes"])
        self.dhcp = DHCP(dhcp["pools"], dhcp["helper_address"], dhcp["excluded_address"])
        
        
    def update(self, hostname: str, ip_mgmt: IPv4Address, security: dict, interfaces: List[dict], users: List[dict] = None, banner: str = None, dhcp: dict = None, routing_process: dict = None) -> None:
        super().update(hostname, ip_mgmt, security, interfaces, users, banner)
        self.routing_process = RoutingProcess(routing_process["ospf_processes"], routing_process["static_routes"])
        self.dhcp = DHCP(dhcp["pools"], dhcp["helper_address"], dhcp["excluded_address"])
        