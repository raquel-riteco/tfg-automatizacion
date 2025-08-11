from typing import List, cast
from ipaddress import IPv4Address, IPv4Network

class OSPF:
    def __init__(self, id: int, bw_cost: int = 10, networks: List[IPv4Network] = None, routing_ip: IPv4Address = None,
                 redistribute: bool = False):
        self.id = id
        self.bw_cost = bw_cost
        self.networks = networks
        self.routing_ip = routing_ip
        self.redistribute = redistribute
        
        
    def update(self, id: int, bw_cost: int = 10, networks: List[dict] = None, routing_ip: IPv4Address = None,
               redistribute: bool = False) -> None:
        """
        Updates the OSPF routing process attributes, including ID, bandwidth cost, networks, routing ID,
        and redistribution setting.

        Args:
            id (int): The OSPF process ID.
            bw_cost (int, optional): Bandwidth cost for the OSPF process, used in route calculation. Defaults to 10.
            networks (List[IPv4Network], optional): List of IPv4 networks to include in the OSPF process.
            routing_ip (IPv4Address, optional): The router ID for OSPF routing identification.
            redistribute (bool, optional): Flag indicating if routes from other protocols should be redistributed into OSPF. Defaults to False.

        Returns:
            None
        """
        self.id = id
        self.bw_cost = bw_cost
        self.networks = networks
        self.routing_ip = routing_ip
        self.redistribute = redistribute

    def get_info(self) -> dict:
        info = dict()
        info['id'] = self.id
        info['bw_cost'] = self.bw_cost
        info['networks'] = list()
        for network in self.networks:
            dictionary = dict()
            dictionary['network'] = network['network'].explode
            dictionary['area'] = network['area']
            info['networks'].append(dictionary)
        if self.routing_ip:
            info['routing_ip'] = self.routing_ip
        else:
            info['routing_ip'] = None
        info['redistribute'] = self.redistribute
        return info



class StaticRoute:
    def __init__(self, destination: IPv4Network, next_hop: IPv4Address, admin_dist: int = 1):
        self.destination = destination
        self.next_hop = next_hop
        self.admin_dist = admin_dist
        
        
    def update(self, destination: IPv4Network, next_hop: IPv4Address, admin_dist: int = 1) -> None:
        """
        Updates the static route attributes, including destination network, next hop address, and administrative distance.

        Args:
            destination (IPv4Network): The destination network for the static route.
            next_hop (IPv4Address): The IP address of the next hop router for the static route.
            admin_dist (int, optional): The administrative distance of the route, which is used to determine the priority of the route. Defaults to 1.

        Returns:
            None
        """
        self.destination = destination
        self.next_hop = next_hop
        self.admin_dist = admin_dist

    def get_info(self) -> dict:
        info = dict()
        if self.destination:
            info['destination'] = self.destination.exploded
        else:
            info['destination'] = None
        if self.next_hop:
            info['next_hop'] = self.next_hop
        else:
            info['next_hop'] = None
        info['admin_dist'] = self.admin_dist
        return info


class RoutingProcess:
    def __init__(self, ospf_processes: List[dict] = None, static_routes: List[dict] = None):
        self.static_routes = List[StaticRoute]
        for static_route in static_routes:
            new_static_route = StaticRoute(static_route["destination"], static_route["next_hop"], static_route["admin_dist"])
            self.static_routes.append(new_static_route)
        self.ospf_processes = List[OSPF]
        for ospf_process in ospf_processes:
            new_ospf_process = OSPF(ospf_process["id"], ospf_process["bw_cost"], ospf_process["networks"], ospf_process["routing_id"], ospf_process["redistribute"])
            self.ospf_processes.append(new_ospf_process)
            
            
    def update(self, ospf_processes: List[dict] = None, static_routes: List[dict] = None) -> None:
        """
        Updates the OSPF processes and static routes with the provided configuration data.

        This function iterates through existing static routes and OSPF processes, updating their attributes
        based on the provided dictionaries. It updates each static route and OSPF process with the specified
        configuration parameters such as destination, next hop, OSPF ID, bandwidth cost, and routing protocols.

        Args:
            ospf_processes (List[dict], optional): A list of dictionaries containing OSPF process configurations.
                Each dictionary should include keys like "id", "bw_cost", "networks", "routing_id", and "redistribute".
            static_routes (List[dict], optional): A list of dictionaries containing static route configurations.
                Each dictionary should include keys like "destination", "next_hop", and "admin_dist".

        Returns:
            None
        """
        for i in range(len(self.static_routes)):
            static_route = cast(StaticRoute, self.static_routes[i])
            static_route.update(static_routes[i]["destination"], static_routes[i]["next_hop"], static_routes[i]["admin_dist"])
        for i in range(len(self.ospf_processes)):
            ospf_process = cast(OSPF, self.ospf_processes[i])
            ospf_process.update(ospf_processes[i]["id"], ospf_processes[i]["bw_cost"], ospf_processes[i]["networks"], ospf_processes[i]["routing_id"], ospf_processes[i]["redistribute"])


    def get_info(self) -> dict:
        info = dict()
        info['ospf'] = self.ospf_processes
        info['static_routes'] = self.static_routes
        return info