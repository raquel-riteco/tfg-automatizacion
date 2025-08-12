from typing import List
from ipaddress import IPv4Address, IPv4Network

from model.device import Device
from model.l3_interface import L3Interface
from model.routing_process import RoutingProcess
from model.dhcp import DHCP

class Router(Device):
    def __init__(self, hostname: str, ip_mgmt: IPv4Address, iface_mgmt: str, security: dict, interfaces: List[dict],
                 users: List[dict] = None, banner: str = None, ip_domain_lookup: bool = False,
                 dhcp: dict = None, routing_process: dict = None):
        super().__init__(hostname, ip_mgmt, iface_mgmt, security, users, banner, ip_domain_lookup)
        self.interfaces = []
        for interface in interfaces:
            new_interface = L3Interface(interface["name"], interface["is_up"], interface["description"],
                                        interface["ip_address"], interface["netmask"], interface["ospf"], interface["l3_redundancy"],
                                        interface["helper_address"])
            self.interfaces.append(new_interface)
        self.routing_process = RoutingProcess(routing_process["ospf_processes"], routing_process["static_routes"])
        self.dhcp = DHCP(dhcp["pools"], dhcp["excluded_address"])
        
        
    def update(self, config_info: dict) -> None:
        super().update(config_info)

        if config_info['iface']:
            if config_info['subiface_num']:
                self.interfaces.append(L3Interface(f"{config_info['iface']}.{config_info['subiface_num']}",
                                                   False))
            else:
                for iface in self.interfaces:
                    if config_info['iface'] == iface.name:
                        iface.update(config_info)
        if config_info['iface_list']:
            for config_iface in config_info['iface_list']:
                for iface in self.interfaces:
                    if config_iface == iface.name:
                        iface.update(config_info)

        self.routing_process.update(config_info)
        self.dhcp.update(config_info)

    def get_device_info(self) -> dict:
        device_info = super().get_device_info()
        device_info["device_type"] = "R"

        device_info["iface_list"] = list()
        for iface in self.interfaces:
            device_info["iface_list"].append(iface.get_info())

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

        # OSPF

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