from typing import List
from ipaddress import IPv4Address, IPv4Network

from model.device import Device
from model.l3_interface import L3Interface
from model.routing_process import RoutingProcess
from model.dhcp import DHCP

class Router(Device):
    def __init__(self, hostname: str, ip_mgmt: IPv4Address, iface_mgmt: str, security: dict, interfaces: List[dict],
                 users: List[dict] = None, banner: str = None, dhcp: dict = None, routing_process: dict = None):
        super().__init__(hostname, ip_mgmt, iface_mgmt, security, users, banner)
        self.interfaces = []
        for interface in interfaces:
            new_interface = L3Interface(interface["name"], interface["is_up"], interface["description"],
                                        interface["ip_address"], interface["ospf"], interface["l3_redundancy"])
            self.interfaces.append(new_interface)
        self.routing_process = RoutingProcess(routing_process["ospf_processes"], routing_process["static_routes"])
        self.dhcp = DHCP(dhcp["pools"], dhcp["helper_address"], dhcp["excluded_address"])
        
        
    def update(self, hostname: str, security: dict, interfaces: List[dict],
               users: List[dict] = None, banner: str = None, dhcp: dict = None, routing_process: dict = None) -> None:
        """
        Updates the device attributes, including hostname, management IP, security settings, interfaces,
        users, banner, DHCP configuration, and routing process details.

        Inherits basic update functionality for hostname, management IP, security, interfaces, users,
        and banner. Additionally, initializes and sets specific configurations for DHCP and routing process.

        Args:
            hostname (str): The hostname of the device.
            security (dict): Security configurations, including encryption settings, console, and VTY access controls.
            interfaces (List[dict]): List of dictionaries for interface configurations.
            users (List[dict], optional): List of dictionaries with user information.
            banner (str, optional): Device banner message.
            interfaces (List[dict]): List of dictionaries containing interface information, where each dictionary has:
                - "name" (str): Interface name.
                - "is_up" (bool): Interface status.
                - "description" (str): Interface description.
                - "ip_address" (IPv4Address): IP address assigned to the interface.
                - "ospf" (bool): Whether OSPF is enabled.
                - "l3_redundancy" (str): Layer 3 redundancy configuration.
            dhcp (dict, optional): DHCP configuration details, including:
                - "pools" (List[dict]): List of DHCP address pools.
                - "helper_address" (IPv4Address): DHCP helper address.
                - "excluded_address" (List[dict]): Excluded address ranges or specific IPs.
            routing_process (dict, optional): Routing process information, including:
                - "ospf_processes" (List[dict]): List of OSPF process configurations.
                - "static_routes" (List[dict]): List of static routes.

        Returns:
            None
        """
        super().update(hostname, security, users, banner)
        if interfaces:
            for new_iface in interfaces:
                for my_iface in self.interfaces:
                    if new_iface['name'] == my_iface.name:
                        if "ip_address" in new_iface:
                            ip = IPv4Address(new_iface.get('ip_address'))
                        else:
                            ip = None
                        my_iface.update(new_iface.get("is_up"), new_iface.get("description"),
                                        ip, new_iface.get('ospf'), new_iface.get('l3_redundancy'))

        if routing_process: self.routing_process.update(routing_process["ospf_processes"],
                                                        routing_process["static_routes"])
        if dhcp: self.dhcp.update(dhcp["pools"], dhcp["helper_address"], dhcp["excluded_address"])
        
        
    def get_device_info(self) -> dict:
        device_info = super().get_device_info()
        device_info["device_type"] = "R"

        device_info["iface_list"] = list()
        for iface in self.interfaces:
            device_info["iface_list"].append(iface.get_info())

        device_info["routing_process"] = self.routing_process.get_info()
        device_info["dhcp"] = self.dhcp.get_info()

        return device_info

    def config(self, configuration: dict) -> list:
        # BASIC AND SECURITY CONFIG
        config_lines = super().config(configuration)

        # IFACE CONFIG
        if "iface" in configuration:
            iface = configuration["iface"]

            # Subinterface creation.
            if "subiface_num" in configuration:
                sub = str(configuration["subiface_num"])
                config_lines += [f"interface {iface}.{sub}"]

            else:
                config_lines += [f"interface {iface}"]

            if "description" in configuration:
                config_lines.append(f"description {configuration['description']}")

            if "ip_addr" in configuration:
                config_lines.append(f"ip address {configuration['ip_addr']} {configuration['mask']}")

            if configuration.get("iface_shutdown") is True:
                config_lines.append("shutdown")
            elif configuration.get("iface_shutdown") is False:
                config_lines.append("no shutdown")

        # HSRP REDUNDANCY
        if ({"hsrp_virtual_ip", "iface_list", "hsrp_group", "hsrp_priority", "hsrp_preempt"}
                <= configuration.keys()):
            grp = configuration["hsrp_group"]
            prio = configuration["hsrp_priority"]
            preempt = configuration["preempt"]
            vip = configuration.get("hsrp_virtual_ip")

            for iface in configuration["iface_list"]:
                config_lines += [f"interface {iface}"]
                config_lines.append(f"standby {grp} ip {vip}")
                config_lines.append(f"standby {grp} priority {prio}")
                config_lines.append(f"standby {grp} preempt" if preempt else f"no standby {grp} preempt")

        # DHCP
        if "helper_address" in configuration and "iface" in configuration:
            config_lines += [f"interface {configuration['iface']}",
                            f"ip helper-address {configuration['helper_address']}"]

        if {"first_excluded_addr", "last_excluded_addr"} <= configuration.keys():
            a = str(configuration["first_excluded_addr"])
            b = str(configuration["last_excluded_addr"])
            if a == b:
                config_lines.append(f"ip dhcp excluded-address {a}")
            else:
                config_lines.append(f"ip dhcp excluded-address {a} {b}")

        if {"pool_name", "pool_network", "pool_gateway_ip"} <= configuration.keys():
            pool = configuration["pool_name"]
            net = configuration["pool_network"]  # can be ip_network or str CIDR
            if isinstance(net, str):
                net = IPv4Network(net, strict=False)
            gw = configuration["pool_gateway_ip"]
            dns = configuration.get("pool_dns_ip")

            config_lines += [
                f"ip dhcp pool {pool}",
                f"network {net.network_address.exploded} {net.netmask.exploded}",
                f"default-router {gw}",
            ]
            if dns:
                config_lines.append(f"dns-server {dns}")

        # STATIC ROUTING

        if {"dest_ip", "next_hop"} <= configuration.keys():
            ad = configuration.get("admin_distance")
            dest = str(configuration["dest_ip"])

            if "/" in dest:
                net = IPv4Network(dest, strict=False)
                dest_ip = net.network_address.exploded
                mask = net.netmask.exploded
            else:
                parts = dest.split()
                if len(parts) == 2:
                    dest_ip, mask = parts
                else:
                    raise ValueError("dest_ip must be 'A.B.C.D/M' or 'A.B.C.D MASK'")

            nh = str(configuration["next_hop"])
            if ad is not None:
                config_lines.append(f"ip route {dest_ip} {mask} {nh} {ad}")
            else:
                config_lines.append(f"ip route {dest_ip} {mask} {nh}")

        # ========== OSPF ==========

        if "process_id" in configuration:
            pid = int(configuration["process_id"])
            # Process mode statements under 'router ospf <pid>'
            if any(k in configuration for k in ("router_id", "reference-bandwidth", "network_ip", "is_redistribute")):
                config_lines.append(f"router ospf {pid}")
                if "router_id" in configuration:
                    config_lines.append(f"router-id {configuration['router_id']}")
                if "reference-bandwidth" in configuration:
                    config_lines.append(f"auto-cost reference-bandwidth {configuration['reference-bandwidth']}")
                if {"network_ip", "network_wildcard", "network_area"} <= configuration.keys():
                    nip = configuration["network_ip"]
                    wc = configuration["network_wildcard"]
                    area = configuration["network_area"]
                    config_lines.append(f"network {nip} {wc} area {area}")
                if configuration.get("is_redistribute") is True:
                    what = configuration.get("redistribute_what", "connected")
                    # add 'subnets' for most protocols
                    if what in ("connected", "static", "rip", "eigrp", "bgp"):
                        config_lines.append(f"redistribute {what} subnets")
                    else:
                        config_lines.append(f"redistribute {what}")

            if isinstance(configuration.get("iface_list"), list) and configuration["iface_list"]:
                # apply per-interface OSPF tuning
                for item in configuration["iface_list"]:
                    name = item.get("iface_name") or item.get("name") or item  # support simple str list
                    ospf = item.get("ospf", {}) if isinstance(item, dict) else {}
                    if not name:
                        continue
                    config_lines += [f"interface {name}"]

                    if "hello_interval" in ospf:
                        config_lines.append(f"ip ospf hello-interval {ospf['hello_interval']}")
                    if "dead_interval" in ospf:
                        config_lines.append(f"ip ospf dead-interval {ospf['dead_interval']}")
                    if "priority" in ospf:
                        config_lines.append(f"ip ospf priority {ospf['priority']}")
                    if "cost" in ospf:
                        config_lines.append(f"ip ospf cost {ospf['cost']}")
                    if ospf.get("is_pint_to_point") is True:
                        config_lines.append("ip ospf network point-to-point")

                passive_ifaces = [
                    (item.get("iface_name") or item.get("name"))
                    for item in configuration["iface_list"]
                    if isinstance(item, dict) and item.get("ospf", {}).get("is_passive") is True
                ]
                if passive_ifaces:
                    config_lines.append(f"router ospf {pid}")
                    for pif in passive_ifaces:
                        config_lines.append(f"passive-interface {pif}")

        return config_lines