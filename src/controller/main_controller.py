from typing import cast

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
        return device_list


    def __get_device_controller__(self, info: dict):
        if info['action_by'] == "id":
            return self.device_controllers[info['identification'] - 1]
        elif info['action_by'] == "name":
            for dev_controller in self.device_controllers:
                name = dev_controller.get_device_info()["device_name"]
                if name == info['identification']:
                    return dev_controller
        elif info['action_by'] == "mgmt_ip":
            for dev_controller in self.device_controllers:
                mgmt_ip = dev_controller.get_device_info()["mgmt_ip"]
                if mgmt_ip == info['identification']:
                    return dev_controller 

    def __generate_subnetting__(self, info: dict) -> list:
        """
        Automatically generates subnets from a base network, allocating address space
        based on the number of devices required per subnet.

        Returns:
            list of IPv4Network: The generated subnets in the original input order.

        Raises:
            ValueError: If there is not enough address space in the base network
                        to accommodate all requested subnets.
        """
        base_network = info["network"]
        devices_per_network = info["list_num_devices"]

        networks = [(i, devices) for i, devices in enumerate(devices_per_network)]

        for j in range(1, len(networks)):
            key = networks[j]
            i = j - 1
            while i >= 0 and networks[i][1] < key[1]:
                networks[i + 1] = networks[i]
                i -= 1
            networks[i + 1] = key

        subnets = []
        current_subnet_pool = [base_network]

        for idx, devices in networks:
            needed_hosts = devices + 2
            prefix = 32
            while (2 ** (32 - prefix)) < needed_hosts:
                prefix -= 1

            for i, pool in enumerate(current_subnet_pool):
                try:
                    new_subnets = list(pool.subnets(new_prefix=prefix))
                    subnet = new_subnets[0]
                    subnets.append((idx, subnet))

                    # Update the subnet pool: remove the used block and add remaining ones
                    del current_subnet_pool[i]
                    current_subnet_pool.extend(new_subnets[1:])
                    break
                except ValueError:
                    continue
            else:
                raise ValueError("Not enough address space in the base network to accommodate all subnets.")

        # Restore original input order based on index
        result = [subnet for _, subnet in sorted(subnets)]
        return result
             
    def start(self) -> None:
        """
        Initializes the system by loading configuration data and setting up devices.

        Displays the start menu, saves default settings, and optionally loads a configuration file.
        For each device in the configuration, creates and configures a `DeviceController` instance
        with connection and configuration details, and appends it to the list of device controllers.

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
                ok = device_controller.create_device(device_info["connect"], device_info.get("config"))
                if ok:
                    self.device_controllers.append(device_controller)
                
                
    def run(self) -> None:
        option = 0
        options = Option()
        while option != options.exit:
            option, info = self.view.main_menu(self.__get_devices_list__())
            match option:
                case 1:
                    # Add device
                    device_controller = DeviceController()
                    device_controller.create_device(info)
                    self.device_controllers.append(device_controller)
                case 2:
                    # Remove device
                    dev_controller = self.__get_device_controller__(info)
                    self.device_controllers.remove(dev_controller)
                case 4:
                    # Modify config
                    dev_controller = self.__get_device_controller__(info)
                    dev_controller.configure_device(self.__get_devices_list__())
                case 5:
                    # Subnetting
                    try:
                        result_subnetting = self.__generate_subnetting__(info)
                        save, filename = self.view.display_subnetting(info, result_subnetting)
                        if save == 1:
                            self.files.save_subnetting(filename, result_subnetting, info)
                    except ValueError as e:
                        self.view.print_error(e.args[0])
        
        self.view.goodbye()