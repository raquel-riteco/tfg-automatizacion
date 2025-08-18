from ipaddress import IPv4Address, IPv4Network
from typing import List

class DHCP:
    def __init__(self, pools: List[dict], excluded_address: List[dict] = None):
        self.excluded_addresses = excluded_address
        self.pools = pools

    def update(self, config_info: dict) -> None:
        if 'first_excluded_addr' in config_info:
            self.excluded_addresses.append({'start': IPv4Address(config_info['first_excluded_addr']),
                                            'end': IPv4Address(config_info['last_excluded_addr']) })
        if 'pool_name' in config_info:
            self.pools.append({'name': config_info['pool_name'],
                               'network': IPv4Network(config_info['pool_network']),
                               'default_router': IPv4Address(config_info['pool_gateway_ip'])})


    def get_info(self) -> dict:
        info = dict()

        info['excluded_address'] = list()
        for excluded in self.excluded_addresses:
            dictionary = dict()
            if excluded.get('start') is not None:
                dictionary['start'] = excluded['start'].exploded
            else:
                dictionary['start'] = None
            if excluded.get('end') is not None:
                dictionary['end'] = excluded['end'].exploded
            else:
                dictionary['end'] = None
            info['excluded_address'].append(dictionary)

        info['pools'] = list()
        for pool in self.pools:
            dictionary = dict()
            if pool.get('network') is not None:
                dictionary['network'] = pool['network'].exploded
            else:
                dictionary['network'] = None
            if pool.get('default_router') is not None:
                dictionary['default_router'] = pool['default_router'].exploded
            else:
                dictionary['default_router'] = None
            dictionary['name'] = pool['name']
            info['pools'].append(dictionary)

        return info

