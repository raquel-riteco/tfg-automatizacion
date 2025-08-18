from typing import List, cast
from ipaddress import IPv4Address, IPv4Network

class OSPF:
    def __init__(self, id: int, bw_cost: int = 100, networks: List[dict] = None, router_id: IPv4Address = None,
                 redistribute: bool = False):
        self.id = id
        self.bw_cost = bw_cost
        if networks is None:
            self.networks = list()
        else:
            self.networks = networks
        self.router_id = router_id
        self.redistribute = redistribute
        

    def update(self, config_info: dict) -> None:
        if 'reference-bandwidth' in config_info: self.bw_cost = config_info['reference-bandwidth']
        if 'network_ip' in config_info:
            self.networks.append({'network': IPv4Network(config_info['network_ip']),
                                  'network_area': config_info['network_area']})
        if 'router_id' in config_info: self.router_id = config_info['router_id']
        if 'is_redistribute' in config_info: self.redistribute = config_info['is_redistribute']


    def get_info(self) -> dict:
        info = dict()
        info['id'] = self.id
        info['bw_cost'] = self.bw_cost
        info['networks'] = list()
        for network in self.networks:
            dictionary = dict()
            dictionary['network'] = network['network'].exploded
            dictionary['area'] = network['network_area']
            info['networks'].append(dictionary)
        if self.router_id:
            info['router_id'] = self.router_id
        else:
            info['router_id'] = None
        info['redistribute'] = self.redistribute
        return info



class StaticRoute:
    def __init__(self, destination: IPv4Network, next_hop: IPv4Address, admin_dist: int = 1):
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
            info['next_hop'] = self.next_hop.exploded
        else:
            info['next_hop'] = None
        info['admin_dist'] = self.admin_dist
        return info


class RoutingProcess:
    def __init__(self, ospf_processes: List[dict] = None, static_routes: List[dict] = None):
        self.static_routes = list()
        for static_route in static_routes:
            new_static_route = StaticRoute(static_route["destination"], static_route["next_hop"],
                                           static_route["admin_dist"])
            self.static_routes.append(new_static_route)
        self.ospf_processes =  list()
        for ospf_process in ospf_processes:
            new_ospf_process = OSPF(ospf_process["process_id"], ospf_process["bw_cost"], ospf_process["networks"],
                                    ospf_process["router_id"], ospf_process["redistribute"])
            self.ospf_processes.append(new_ospf_process)
            
            
    def update(self, config_info: dict) -> None:
        if 'dest_ip' in config_info and 'next_hop' in config_info and 'admin_distance' in config_info:
            self.static_routes.append(StaticRoute(IPv4Network(config_info['dest_ip']),
                                                  IPv4Address(config_info['next_hop']),
                                                  config_info['admin_distance']))

        if 'process_id' in config_info:
            found = False
            for ospf_process in self.ospf_processes:
                if ospf_process.id == config_info['process_id']:
                    ospf_process.update(config_info)
                    found = True
                    break
            if not found:
                networks = None
                if 'network_ip' in config_info:
                    networks = list()
                    networks.append({'network_ip': IPv4Network(config_info['network_ip']),
                                     'network_area': config_info['network_area']})
                new_process = OSPF(config_info['process_id'], config_info.get("reference-bandwidth"), networks,
                                   config_info.get('router_id'), config_info.get('is_redistribute'))
                self.ospf_processes.append(new_process)


    def get_info(self) -> dict:
        info = dict()
        info['ospf'] = list()
        for ospf in self.ospf_processes:
            info['ospf'].append(ospf.get_info())
        info['static_routes'] = list()
        for static_route in self.static_routes:
            info['static_routes'].append(static_route.get_info())
        return info