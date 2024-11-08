from typing import List

from src.model.yaml_files import YAMLFiles
from src.model.json_files import JSONFiles

from src.view.view import View

from device_controller import DeviceController

class MainController:
    def __init__(self):
        self.yaml_files = YAMLFiles()
        self.json_files = JSONFiles()
        self.view = View()
        self.device_controllers = List[DeviceController]
        
        
        