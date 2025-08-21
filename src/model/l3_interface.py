from ipaddress import IPv4Address

from model.interface import Interface


class L3Interface(Interface):
    """
    Extends the base Interface class to include Layer 3 configuration attributes such as IP address,
    subnet mask, OSPF parameters, HSRP settings, and DHCP helper addresses.
    """

    def __init__(self, name: str, is_up: bool, description: str = None, ip_addr: IPv4Address = None,
                 netmask: IPv4Address = None, ospf: dict = None, l3_redundancy: dict = None,
                 helper_address: IPv4Address = None):
        """
        Initializes a Layer 3 interface with additional routing-related attributes.

        Args:
            name (str): Name of the interface.
            is_up (bool): Operational status of the interface.
            description (str, optional): Interface description.
            ip_addr (IPv4Address, optional): IP address assigned to the interface.
            netmask (IPv4Address, optional): Netmask of the interface.
            ospf (dict, optional): OSPF parameters.
            l3_redundancy (dict, optional): HSRP configuration.
            helper_address (IPv4Address, optional): DHCP relay IP address.
        """
        super().__init__(name, is_up, description)
        self.ip_address = ip_addr
        self.netmask = netmask
        self.ospf = ospf
        self.l3_redundancy = l3_redundancy
        self.helper_address = helper_address

    def update(self, config_info: dict) -> None:
        """
        Updates the Layer 3 interface configuration with new values from a config dictionary.

        Args:
            config_info (dict): Dictionary containing interface configuration updates.
        """
        super().update(config_info)

        if 'ip_address' in config_info: self.ip_address = IPv4Address(config_info['ip_address'])
        if 'mask' in config_info: self.netmask = IPv4Address(config_info['mask'])

        if 'hsrp_group' in config_info:
            self.l3_redundancy['hsrp_group'] = config_info['hsrp_group']
            self.l3_redundancy['hsrp_virtual_ip'] = IPv4Address(config_info['hsrp_virtual_ip'])
            self.l3_redundancy['hsrp_priority'] = config_info['hsrp_priority']
            self.l3_redundancy['preempt'] = config_info['preempt']

        if 'ospf' in config_info:
            if 'hello_interval' in config_info['ospf']:
                self.ospf['hello_interval'] = config_info['ospf']['hello_interval']
            if 'dead_interval' in config_info['ospf']:
                self.ospf['dead_interval'] = config_info['ospf']['dead_interval']
            if 'is_passive' in config_info['ospf']:
                self.ospf['is_passive'] = config_info['ospf']['is_passive']
            if 'priority' in config_info['ospf']:
                self.ospf['priority'] = config_info['ospf']['priority']
            if 'cost' in config_info['ospf']:
                self.ospf['cost'] = config_info['ospf']['cost']
            if 'is_pint_to_point' in config_info['ospf']:
                self.ospf['is_pint_to_point'] = config_info['ospf']['is_pint_to_point']

        if 'helper_address' in config_info: self.helper_address = IPv4Address(config_info['helper_address'])

    def get_info(self) -> dict:
        """
        Returns a dictionary with full interface information including IP, OSPF, and redundancy.

        Returns:
            dict: Dictionary with all interface attributes, including Layer 3 fields.
        """
        # When config is empty
        # ip_address is None
        # netmask is None
        # ospf is dict with
        # hello_interval is None
        # dead_interval is None
        # is_passive is False
        # priority is None
        # cost is None
        # is point_to_point is False
        # l3_redundancy is dict with:
        # hsrp_group is None
        # hsrp_virtual_ip is None
        # hsrp_priority is None
        # preempt is None
        # helper_address is None

        info = super().get_info()

        if self.ip_address is not None:
            info['ip_address'] = self.ip_address.exploded
        else:
            info['ip_address'] = None
        if self.netmask is not None:
            info['netmask'] = self.netmask.exploded
        else:
            info['netmask'] = None
        info['ospf'] = self.ospf
        info['l3_redundancy'] = self.l3_redundancy
        if self.helper_address is not None:
            info['helper_address'] = self.helper_address.exploded
        else:
            info['helper_address'] = None
        return info

    def get_config(self) -> dict:
        """
        Returns a dictionary with only the attributes that should be used for applying config changes.

        Returns:
            dict: Dictionary with configurable Layer 3 attributes.
        """
        info = super().get_info()
        if self.ip_address is not None:
            info['ip_address'] = self.ip_address.exploded
        if self.netmask is not None:
            info['netmask'] = self.netmask.exploded

        info['ospf'] = dict()
        if self.ospf['hello_interval'] is not None:
            info['hello_interval'] = self.ospf['hello_interval']
        if self.ospf['dead_interval'] is not None:
            info['dead_interval'] = self.ospf['dead_interval']
        if self.ospf['is_passive'] is True:
            info['is_passive'] = self.ospf['is_passive']
        if self.ospf['priority'] is not None:
            info['priority'] = self.ospf['priority']
        if self.ospf['cost'] is not None:
            info['cost'] = self.ospf['cost']
        if self.ospf['is_point_to_point'] is True:
            info['is_point_to_point'] = self.ospf['is_point_to_point']
        if len(info['ospf']) == 0:
            info.pop('ospf')

        if self.l3_redundancy['hsrp_group'] is not None:
            info['l3_redundancy'] = dict()
            info['l3_redundancy']['hsrp_group'] = self.l3_redundancy['hsrp_group']
            if self.l3_redundancy['preempt'] is True:
                info['l3_redundancy']['preempt'] = self.l3_redundancy['preempt']
            info['l3_redundancy']['hsrp_virtual_ip'] = self.l3_redundancy['hsrp_virtual_ip'].exploded
            info['l3_redundancy']['hsrp_priority'] = self.l3_redundancy['hsrp_priority']
        if self.helper_address is not None:
            info['helper_address'] = self.helper_address.exploded

        return info

