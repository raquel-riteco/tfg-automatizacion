from typing import List, cast

from model.files import Files
from view.view import View, Option
from controller.device_controller import DeviceController
from model.subnetting import Subnetting


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
        return device_list
             
        
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
        load_config, info = self.view.start_menu()
        self.files.save_defaults_file(info["defaults"])
        if load_config:
            info = self.files.load_config(info["filename"])
            for device in info:
                device_info = info[device]
                device_controller = DeviceController()
                # Important to call get and not pass the param directly because there may not exist a key "config" in
                # the device_info dictionary.
                device_controller.create_device(device_info["connect"], device_info.get("config"))
                self.device_controllers.append(device_controller)
                
                
    def run(self) -> None:
        option = 0
        options = Option()
        while option != options.exit:  
            option, info = self.view.main_menu(self.__get_devices_list__())
            match option:
                case 1:
                    # Implement add device
                    pass
                case 2:
                    # Implement remove device
                    pass
                case 4:
                    # Implement modify config

                    pass
                case 5:
                    subnetting = Subnetting(info)
                    try:
                        result_subnetting = subnetting.generate_subnetting()
                        self.view.display_subnetting(info, result_subnetting)
                    except ValueError as e:
                        self.view.print_error(e.args[0])
        
        self.view.goodbye()