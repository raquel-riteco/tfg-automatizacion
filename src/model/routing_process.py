from typing import List
from ipaddress import IPv4Address, IPv4Network


class OSPF:
    def __init__(self, id: int, bw_cost: int = 100, networks: List[dict] = None, router_id: IPv4Address = None,
                 redistribute: bool = False):
        """
        Initialize an OSPF routing process.

        Args:
            id (int): The OSPF process ID.
            bw_cost (int): Reference bandwidth cost. Defaults to 100.
            networks (List[dict], optional): List of OSPF network dictionaries.
            router_id (IPv4Address, optional): Router ID.
            redistribute (bool): Flag for static route redistribution.
        """
        self.id = id
        self.bw_cost = bw_cost
        self.networks = networks if networks else []
        self.router_id = router_id
        self.redistribute = redistribute

    def update(self, config_info: dict) -> None:
        """
        Update the OSPF process settings with the given configuration dictionary.
        """
        if 'reference-bandwidth' in config_info:
            self.bw_cost = config_info['reference-bandwidth']
        if 'network_ip' in config_info:
            self.networks.append({'network': IPv4Network(config_info['network_ip']),
                                  'network_area': config_info['network_area']})
        if 'router_id' in config_info:
            self.router_id = config_info['router_id']
        if 'is_redistribute' in config_info:
            self.redistribute = config_info['is_redistribute']

    def get_info(self) -> dict:
        """
        Returns the OSPF configuration details in dictionary format.

        Returns:
            dict: OSPF configuration details.
        """
        info = dict()
        info['id'] = self.id
        info['bw_cost'] = self.bw_cost
        info['networks'] = [{'network': net['network'].exploded, 'area': net['network_area']} for net in self.networks]
        info['router_id'] = self.router_id if self.router_id else None
        info['redistribute'] = self.redistribute
        return info


class StaticRoute:
    def __init__(self, destination: IPv4Network, next_hop: IPv4Address, admin_dist: int = 1):
        """
        Initialize a static route.

        Args:
            destination (IPv4Network): Destination network.
            next_hop (IPv4Address): Next-hop IP address.
            admin_dist (int): Administrative distance. Defaults to 1.
        """
        self.destination = destination
        self.next_hop = next_hop
        self.admin_dist = admin_dist

    def get_info(self) -> dict:
        """
        Returns the static route configuration details in dictionary format.

        Returns:
            dict: Static route configuration.
        """
        return {
            'destination': self.destination.exploded if self.destination else None,
            'next_hop': self.next_hop.exploded if self.next_hop else None,
            'admin_dist': self.admin_dist
        }


class RoutingProcess:
    def __init__(self, ospf_processes: List[dict] = None, static_routes: List[dict] = None):
        """
        Initialize routing processes, including OSPF and static routes.

        Args:
            ospf_processes (List[dict], optional): List of OSPF process configurations.
            static_routes (List[dict], optional): List of static route configurations.
        """
        self.static_routes = [StaticRoute(sr["destination"], sr["next_hop"], sr["admin_dist"]) for sr in static_routes] if static_routes else []
        self.ospf_processes = [
            OSPF(o["process_id"], o["bw_cost"], o["networks"], o["router_id"], o["redistribute"])
            for o in ospf_processes
        ] if ospf_processes else []

    def update(self, config_info: dict) -> None:
        """
        Update routing processes based on the given configuration dictionary.
        Adds new static routes or modifies existing OSPF processes.
        """
        if {'dest_ip', 'next_hop', 'admin_distance'} <= config_info.keys():
            self.static_routes.append(StaticRoute(
                IPv4Network(config_info['dest_ip']),
                IPv4Address(config_info['next_hop']),
                config_info['admin_distance'])
            )

        if 'process_id' in config_info:
            for ospf in self.ospf_processes:
                if ospf.id == config_info['process_id']:
                    ospf.update(config_info)
                    return

            networks = None
            if 'network_ip' in config_info:
                networks = [{'network': IPv4Network(config_info['network_ip']),
                             'network_area': config_info['network_area']}]
            self.ospf_processes.append(OSPF(
                config_info['process_id'],
                config_info.get('reference-bandwidth'),
                networks,
                config_info.get('router_id'),
                config_info.get('is_redistribute')
            ))

    def get_info(self) -> dict:
        """
        Returns complete information about the routing processes.

        Returns:
            dict: Dictionary with lists of OSPF and static route configurations.
        """
        return {
            'ospf': [ospf.get_info() for ospf in self.ospf_processes],
            'static_routes': [route.get_info() for route in self.static_routes]
        }

    def get_config(self) -> dict | None:
        """
        Returns the configuration details of routing processes.
        Returns None if both OSPF and static routes are empty.

        Returns:
            dict | None: The routing process configuration or None.
        """
        ospf_configs = [ospf.get_info() for ospf in self.ospf_processes]
        static_configs = [route.get_info() for route in self.static_routes]

        if not ospf_configs and not static_configs:
            return None

        result = {}
        if ospf_configs:
            result['ospf'] = ospf_configs
        if static_configs:
            result['static_routes'] = static_configs

        return result

