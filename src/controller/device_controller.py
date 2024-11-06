from src.model.connector import Connector
from src.model.device import Device

class DeviceController:
    def __init__(self, device: Device):
        self.connector = Connector()
        self.device = device
        