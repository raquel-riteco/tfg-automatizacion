from device import Device
from routing_process import RoutingProcess
from dhcp import DHCP

class Router(Device):
    def __init__(self, dhcp: DHCP = None, routing_process: RoutingProcess = None):
        super().__init__()
        self.routing_process = routing_process
        self.dhcp = dhcp
        