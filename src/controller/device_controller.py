from model.connector import Connector
from model.router import Router
from view.router_menu import RouterMenu
from view.view import Option as options
from view.view import View

class DeviceController:
    def __init__(self):
        self.device = None
        self.connector = Connector()
        self.menu = None
        self.view = View()


    def create_device(self, device_info: dict, device_config: dict = None) -> None:
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
            device_config (dict, optional)
        Returns:
            None
        """
        try:
            connector_info = self.connector.get_device_info(device_info)
            if device_info["device_type"] == "router":
                self.menu = RouterMenu()
                self.device = Router(device_info["name"], device_info["mgmt_ip"], device_info["mgmt_iface"],
                                     connector_info["security"], connector_info["interfaces"],
                                     connector_info["users"], connector_info["banner"], connector_info["dhcp"],
                                     connector_info["routing_process"])
                if device_config and len(device_config) > 0:
                    # Important to call get and not pass the params directly because they may not exist in the
                    # device_config dictionary.
                    self.device.update(device_info["name"], device_config.get("security"),
                                       device_config.get("interfaces"), device_config.get("users"),
                                       device_config.get("banner"), device_config.get("dhcp"),
                                       device_config.get("routing_process"))
                    self.device.config(device_config)



        except RuntimeError as e:
            self.view.print_error(str(e))


    def configure_device(self) -> None:
        if type(self.device) == type(Router):
            returned = self.menu.show_router_menu()
            if returned != options.exit:
                str_option, info = returned
                match str_option:
                    case "device_name":
                        pass
                    case "ip_domain":
                        pass
                    case "add_user":
                        pass
                    case "remove_user":
                        pass
                    case "banner_motd":
                        pass
                    case "iface_ip_address":
                        pass
                    case "subiface_config":
                        pass
                    case "iface_description":
                        pass
                    case "redundancy_config":
                        pass
                    case "static_routing":
                        pass
                    case "ospf_iface_hello":
                        pass
                    case "ospf_iface_dead":
                        pass
                    case "ospf_iface_passive":
                        pass
                    case "ospf_iface_priority":
                        pass
                    case "ospf_iface_cost":
                        pass
                    case "ospf_iface_point_to_point":
                        pass
                    case "ospf_process_reference":
                        pass
                    case "ospf_process_network":
                        pass
                    case "ospf_process_id":
                        pass
                    case "ospf_process_redistr":
                        pass
                    case "dhcp_helper_addr":
                        pass
                    case "dhcp_exclude_addr":
                        pass
                    case "dhcp_pool":
                        pass

                    
    def get_device_info(self) -> dict:
        return self.device.get_device_info()