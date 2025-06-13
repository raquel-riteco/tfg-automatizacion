from model.connector import Connector
from model.router import Router
from view.view import View

class DeviceController:
    def __init__(self):
        self.connector = Connector()
        self.view = View()
        
        
    def create_device(self, device_info: dict) -> None:
        """
        Creates a device instance based on the provided device information.

        Connects to the device to retrieve additional information and initializes a `Router` object
        if the device type is identified as "router".

        Args:
            device_info (dict): A dictionary containing the device's attributes, including:
                - "device_type" (str): Type of the device, e.g., "router".
                - "name" (str): Device name.
                - "mgmt_ip" (str): Management IP address.
                - "mgmt_iface" (str): Management interface.

        Returns:
            None
        """
        try:
            connector_info = self.connector.get_device_info(device_info)
        except RuntimeError as e:
            self.view.print_error(e)

        if device_info["device_type"] == "router":
            '''
            self.device = Router(device_info["name"], device_info["mgmt_ip"], device_info["mgmt_iface"], 
                                 connector_info["security"], connector_info["interfaces"], connector_info["users"], 
                                 connector_info["banner"], connector_info["dhcp"], connector_info["routing_process"])
            '''
        
    def configure_device(self, config_info: dict) -> None:
        pass
    
    
    def get_device_info(self) -> dict:
        return self.device.get_device_info()