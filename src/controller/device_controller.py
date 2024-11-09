from src.model.connector import Connector
from src.model.router import Router

class DeviceController:
    def __init__(self):
        self.connector = Connector()
        
        
    def create_device(self, device_info: dict) -> None:
        # Connect to device to get information
        connector_info = self.connector.get_device_info()
        if device_info["device_type"] == "router":
            self.device = Router(device_info["name"], device_info["ip_mgmt"], device_info["iface_mgmt"], 
                                 connector_info["security"], connector_info["interfaces"], connector_info["users"], 
                                 connector_info["banner"], connector_info["dhcp"], connector_info["routing_process"])
        
        
    def configure_device(self, config_info: dict) -> None:
        pass
    