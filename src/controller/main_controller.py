from typing import List, cast

from model.files import Files
from view.view import View, Option
from controller.device_controller import DeviceController



class MainController:
    def __init__(self):
        self.files = Files()
        self.view = View()
        self.device_controllers = list()
        
    
    def __get_devices_list__(self) -> list:
        device_list = list()
        for i in range(len(self.device_controllers)):
            dev_controller = cast(DeviceController, self.device_controllers[i])
            device_dict = dev_controller.get_device_info()
            device_list.append(device_dict)
             
        
    def start(self) -> None:
        """
        Initializes the system by loading configuration data and setting up devices.

        Displays the start menu, saves default settings, and optionally loads a configuration file.
        For each device in the configuration, creates and configures a `DeviceController` instance
        with connection and configuration details, and appends it to the list of device controllers.

        Args:
            None

        Returns:
            None
        """
        info = dict()
        load_config = self.view.start_menu(info)
        self.files.save_defaults_file(info["defaults"])
        if load_config:
            info = self.files.load_config(info["filename"])
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
            option = self.view.main_menu(info, self.__get_devices_list__())
        
        self.view.goodbye()