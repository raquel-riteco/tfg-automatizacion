from ipaddress import IPv4Address

from model.interface import Interface


class L3Interface(Interface):
    def __init__(self, name: str, is_up: bool, description: str = None, ip_addr: IPv4Address = None,
                 netmask: IPv4Address = None, ospf: dict = None, l3_redundancy: dict = None,
                 helper_address: IPv4Address = None):
        super().__init__(name, is_up, description)
        self.ip_address = ip_addr
        self.netmask = netmask
        self.ospf = ospf
        self.l3_redundancy = l3_redundancy
        self.helper_address = helper_address
        
        
    def update(self, config_info: dict) -> None:
        super().update(config_info)

        if config_info['ip_addr']: self.ip_address = IPv4Address(config_info['ip_addr'])
        if config_info['netmask']: self.netmask = IPv4Address(config_info['netmask'])

        if config_info['hsrp_group']:
            self.l3_redundancy['hsrp_group'] = config_info['hsrp_group']
            self.l3_redundancy['hsrp_virtual_ip'] = IPv4Address(config_info['hsrp_virtual_ip'])
            self.l3_redundancy['hsrp_priority'] = config_info['hsrp_priority']
            self.l3_redundancy['preempt'] = config_info['preempt']

        if config_info['ospf']:
            if config_info['ospf']['hello_interval']:
                self.ospf['hello_interval'] = config_info['ospf']['hello_interval']
            if config_info['ospf']['dead_interval']:
                self.ospf['dead_interval'] = config_info['ospf']['dead_interval']
            if config_info['ospf']['is_passive']:
                self.ospf['is_passive'] = config_info['ospf']['is_passive']
            if config_info['ospf']['priority']:
                self.ospf['priority'] = config_info['ospf']['priority']
            if config_info['ospf']['cost']:
                self.ospf['cost'] = config_info['ospf']['cost']
            if config_info['ospf']['is_pint_to_point']:
                self.ospf['is_pint_to_point'] = config_info['ospf']['is_pint_to_point']

        if config_info['helper_address']: self.helper_address = IPv4Address(config_info['helper_address'])


    def get_info(self) -> dict:
        info = super().get_info()
        if self.ip_address:
            info['ip_addr'] = self.ip_address.exploded
        else:
            info['ip_addr'] = None
        if self.netmask:
            info['netmask'] = self.netmask.exploded
        else:
            info['netmask'] = None
        info['ospf'] = self.ospf
        info['l3_redundancy'] = self.l3_redundancy
        if self.helper_address:
            info['helper_address'] = self.helper_address.exploded
        return info