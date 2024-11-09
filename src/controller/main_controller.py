from typing import List

from src.model.files import Files
from src.view.view import View, Option
from device_controller import DeviceController



class MainController:
    def __init__(self):
        self.files = Files()
        self.view = View()
        self.device_controllers = List[DeviceController]
        
        
    def start(self) -> None:
        info = dict()
        load_config = self.view.start_menu(info)
        self.files.save_defaults_file()
        if load_config:
            info = self.files.load_config()
            for device in info:
                device_info = info[device]
                device_controller = DeviceController()
                device_controller.create_device(device_info["connect"])
                device_controller.configure_device(device_info["config"])
                self.device_controllers.append(device_controller)
                
                
    def run(self) -> None:
        option = 0
        options = Option()
        info = dict()
        while option != options.exit:  
            option = self.view.main_menu(info)
        
        self.view.goodbye()