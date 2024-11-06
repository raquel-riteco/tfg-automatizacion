from device import Device
from routing_process import RoutingProcess
from dhcp import DHCP

class Router(Device):
    def __init__(self):
        super().__init__()
        self.routing_process = RoutingProcess()
        self.dhcp = DHCP()
        