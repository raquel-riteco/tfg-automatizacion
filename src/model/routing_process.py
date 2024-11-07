from typing import List
from ipaddress import IPv4Address, IPv4Network

class OSPF:
    def __init__(self, id: int, bw_cost: int = 10, networks: List[IPv4Network] = None, routing_id: IPv4Address = None, redistribute: bool = False):
        self.id = id
        self.bw_cost = bw_cost
        self.networks = networks
        self.routing_id = routing_id
        self.redistribute = redistribute


class StaticRoute:
    def __init__(self, destination: IPv4Network, next_hop: IPv4Address, admin_dist: int = 1):
        self.destination = destination
        self.next_hop = next_hop
        self.admin_dist = admin_dist


class RoutingProcess:
    def __init__(self, ospf_processes: List[OSPF] = None, static_routes: List[StaticRoute] = None):
        self.static_routes = static_routes
        self.ospf_processes = ospf_processes