from ipaddress import IPv4Address, IPv4Network
from typing import List


class DHCP:
    """
    Represents the DHCP configuration for a network device.

    This class stores DHCP excluded addresses and DHCP pools, and provides
    methods to update, retrieve, and export that configuration.
    """
    def __init__(self, pools: List[dict], excluded_address: List[dict] = None):
        """
        Initialize the DHCP configuration.

        Args:
            pools (List[dict]): List of DHCP pool definitions.
            excluded_address (List[dict], optional): List of excluded address ranges.
        """
        self.excluded_addresses = excluded_address
        self.pools = pools

    def update(self, config_info: dict) -> None:
        """
        Update the DHCP configuration with new excluded addresses or pools.

        Args:
            config_info (dict): Dictionary with keys:
                - 'first_excluded_addr': IPv4 address marking start of range.
                - 'last_excluded_addr': IPv4 address marking end of range.
                - 'pool_name': Name of the DHCP pool.
                - 'pool_network': Network assigned to the pool.
                - 'pool_gateway_ip': Default gateway for the pool.
        """
        if 'first_excluded_addr' in config_info:
            self.excluded_addresses.append({'start': IPv4Address(config_info['first_excluded_addr']),
                                            'end': IPv4Address(config_info['last_excluded_addr'])})
        if 'pool_name' in config_info:
            self.pools.append({'name': config_info['pool_name'],
                               'network': IPv4Network(config_info['pool_network']),
                               'default_router': IPv4Address(config_info['pool_gateway_ip'])})

    def get_info(self) -> dict:
        """
        Returns a readable version of the current DHCP configuration.

        Returns:
            dict: Includes 'excluded_address' and 'pools' with string representations.
        """
        info = dict()

        # When config is empty
        # excluded_address is empty list
        # pools is empty list

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

    def get_config(self) -> dict | None:
        """
        Returns the configuration data in exportable format.

        Returns:
            dict | None: Returns None if no config exists. Otherwise, returns:
                - 'excluded_address': List of address ranges.
                - 'pools': List of DHCP pools.
        """
        if len(self.excluded_addresses) == 0 and len(self.pools) == 0:
            return None

        info = dict()
        info['excluded_address'] = list()
        for excluded in self.excluded_addresses:
            dictionary = dict()
            if excluded.get('start') is not None:
                dictionary['start'] = excluded['start'].exploded
            if excluded.get('end') is not None:
                dictionary['end'] = excluded['end'].exploded
            info['excluded_address'].append(dictionary)

        if len(info['excluded_address']) == 0:
            info.pop('excluded_address')

        info['pools'] = list()
        for pool in self.pools:
            dictionary = dict()
            if pool.get('network') is not None:
                dictionary['network'] = pool['network'].exploded
            if pool.get('default_router') is not None:
                dictionary['default_router'] = pool['default_router'].exploded
            dictionary['name'] = pool['name']
            info['pools'].append(dictionary)

        if len(info) == 0:
            return None

        return info

