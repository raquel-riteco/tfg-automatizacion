from typing import List
from ipaddress import IPv4Address, IPv4Network

import re
from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get
from ciscoconfparse import CiscoConfParse

from model.device import Device
from model.l3_interface import L3Interface
from model.routing_process import RoutingProcess
from model.dhcp import DHCP
from model.interface import normalize_iface


class Router(Device):
    """
    Router class representing a network router device.

    Inherits from the Device class and extends it with:
        - Layer 3 interface configuration
        - DHCP setup and exclusions
        - Routing configuration (OSPF, static)

    This class supports dynamic configuration generation and verification
    using parsed information from Cisco IOS running-config outputs.
    """
    def __init__(self, device_name: str, ip_mgmt: IPv4Address, iface_mgmt: str, security: dict, interfaces: List[dict],
                 users: List[dict] = None, banner: str = None, ip_domain_lookup: bool = False,
                 dhcp: dict = None, routing_process: dict = None):
        """
        Initializes the Router object with provided configuration and component objects.

        Args:
            device_name (str): Router hostname.
            ip_mgmt (IPv4Address): Management IP.
            iface_mgmt (str): Management interface.
            security (dict): Security config dict.
            interfaces (List[dict]): List of interface configs.
            users (List[dict], optional): List of user entries.
            banner (str, optional): MOTD banner.
            ip_domain_lookup (bool, optional): Enable/disable DNS lookup.
            dhcp (dict, optional): DHCP configuration dict.
            routing_process (dict, optional): Routing process config.
        """
        super().__init__(device_name, ip_mgmt, iface_mgmt, security, users, banner, ip_domain_lookup)
        self.interfaces = []
        for interface in interfaces:
            new_interface = L3Interface(interface["name"], interface["is_up"], interface["description"],
                                        interface["ip_address"], interface["netmask"], interface["ospf"],
                                        interface["l3_redundancy"], interface["helper_address"])
            self.interfaces.append(new_interface)
        self.routing_process = RoutingProcess(routing_process["ospf_processes"], routing_process["static_routes"])
        self.dhcp = DHCP(dhcp["pools"], dhcp["excluded_address"])


    def update(self, config_info: dict) -> None:
        """
        Update the router configuration state based on a configuration dictionary.

        Applies updates to:
            - The router base configuration (name, security, etc.)
            - Specific interfaces (single or multiple)
            - Routing process settings (OSPF/static)
            - DHCP settings (pools, exclusions)

        Args:
            config_info (dict): Configuration fields and values to update the internal router state.
        """
        super().update(config_info)

        if 'iface' in config_info:
            if 'subiface_num' in config_info:
                self.interfaces.append(L3Interface(f"{config_info['iface']}.{config_info['subiface_num']}",
                                                   False))
            else:
                for iface in self.interfaces:
                    if normalize_iface(config_info['iface']) == iface.name:
                        iface.update(config_info)
        if 'iface_list' in config_info:
            for config_iface in config_info['iface_list']:
                for iface in self.interfaces:
                    if config_iface == iface.name:
                        iface.update(config_info)

        self.routing_process.update(config_info)
        self.dhcp.update(config_info)

    def get_device_info(self) -> dict:
        """
        Collect the current operational information from the router.

        Returns a dictionary representing the full state of the router, including:
            - Device identity and platform
            - Management interface and IP
            - Users, banner, security settings
            - All configured L3 interfaces
            - Routing (OSPF/static) configuration
            - DHCP configuration (pools, excluded addresses)

        Returns:
        dict: Complete router info as expected by higher-level logic/UI.
        """
        device_info = super().get_device_info()
        device_info["device_type"] = "R"

        # When config is empty
        # interfaces is list
        #

        device_info["interfaces"] = list()
        for iface in self.interfaces:
            device_info["interfaces"].append(iface.get_info())

        device_info["dhcp"] = self.dhcp.get_info()
        device_info["routing"] = self.routing_process.get_info()

        return device_info

    def get_config(self) -> dict:
        """
        Extract the current intended configuration that can be pushed/applied to the router.

        Returns a dictionary with all configured parameters, including:
            - Device name, users, encryption, banner, etc.
            - Interfaces (excluding management interface)
            - DHCP configuration (only if present)
            - Routing configuration (only if present)

        Returns:
            dict: The router's full configuration dictionary
        """
        device_config = super().get_config()

        interfaces = list()
        for iface in self.interfaces:
            if iface.name != self.mgmt_iface:
                iface_config = iface.get_config()
                if iface_config is not None:
                    interfaces.append(iface_config)
        if len(interfaces) > 0:
            device_config['interfaces'] = interfaces

        dhcp = self.dhcp.get_config()
        if dhcp is not None:
            device_config['dhcp'] = dhcp
        routing = self.routing_process.get_config()
        if routing is not None:
            device_config["routing"] = routing

        return device_config


    def config(self, configuration: dict) -> list:
        """
        Verifies whether the intended configuration has been correctly applied to the router.
        Inherits base checks from Device and adds validation for interface, DHCP,
        static routing and OSPF using CiscoConfParse.

        Args:
            configuration (dict): The configuration dictionary.

        Returns:
            dict: Dictionary with boolean results per configuration item.
        """

        # BASIC AND SECURITY CONFIG
        config_lines = super().config(configuration)

        # IFACE CONFIG
        if "iface" in configuration:
            iface = configuration["iface"]

            # Subinterface creation.
            if "subiface_num" in configuration:
                sub = str(configuration["subiface_num"])
                config_lines += [f"interface {iface}.{sub}"]
                config_lines += [f"encapsulation dot1Q {sub}"]

            else:
                config_lines += [f"interface {iface}"]

            if "description" in configuration:
                config_lines.append(f"description {configuration['description']}")

            if "ip_address" in configuration:
                config_lines.append(f"ip address {configuration['ip_address']} {configuration['mask']}")

            if configuration.get("is_up") is False:
                config_lines.append("shutdown")
            elif configuration.get("is_up") is True:
                config_lines.append("no shutdown")

            # HSRP REDUNDANCY
            if ({"hsrp_virtual_ip", "hsrp_group", "hsrp_priority", "preempt"}
                    <= configuration.keys()):
                grp = configuration["hsrp_group"]
                prio = configuration["hsrp_priority"]
                preempt = configuration["preempt"]
                vip = configuration.get("hsrp_virtual_ip")

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

            net = IPv4Network(dest, strict=False)
            dest_ip = net.network_address.exploded
            mask = net.netmask.exploded

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
                if {"network_ip", "network_area"} <= configuration.keys():
                    net = IPv4Network(configuration["network_ip"], strict=False)
                    nip = net.network_address.exploded
                    wc = net.hostmask.exploded

                    area = configuration["network_area"]
                    config_lines.append(f"network {nip} {wc} area {area}")
                if configuration.get("is_redistribute") is True:
                    config_lines.append(f"redistribute static subnet")
                elif configuration.get("is_redistribute") is False:
                    config_lines.append(f"no redistribute static subnet")

        if "iface_list" in configuration:
            passive_ifaces = []
            for item in configuration["iface_list"]:
                iface_name = item['name']
                config_lines += [f"interface {iface_name}"]

                if "hello_interval" in configuration[iface_name]:
                    config_lines.append(f"ip ospf hello-interval {configuration[iface_name]['hello_interval']}")
                if "dead_interval" in configuration[iface_name]:
                    config_lines.append(f"ip ospf dead-interval {configuration[iface_name]['dead_interval']}")
                if "priority" in configuration[iface_name]:
                    config_lines.append(f"ip ospf priority {configuration[iface_name]['priority']}")
                if "cost" in configuration[iface_name]:
                    config_lines.append(f"ip ospf cost {configuration[iface_name]['cost']}")
                if configuration[iface_name].get("is_pint_to_point") is True:
                    config_lines.append("ip ospf network point-to-point")
                if configuration[iface_name].get("is_passive") is True:
                    passive_ifaces.append(iface_name)

            if len(passive_ifaces) != 0:
                pid = configuration['process_id']
                config_lines.append(f"router ospf {pid}")
                for pif in passive_ifaces:
                    config_lines.append(f"passive-interface {pif}")

        return config_lines

    def verify_config_applied(self, configuration: dict) -> dict:
        """
        Verifies whether the intended configuration has been applied to the router.
        Extends the base Device.verify_config_applied() with router-specific checks:
        - Interface & subinterface config (description, IP, shutdown)
        - HSRP (group IP, priority, preempt)
        - DHCP (helper-address, excluded-address, pool settings)
        - Static routing
        - OSPF (process config and per-interface settings, passive-ifaces)
        """

        nr = InitNornir(config_file="config/config.yaml")
        target = nr.filter(name=self.device_name)

        result = target.run(task=napalm_get, getters=["config"])
        task_result = result[self.device_name]
        if task_result.failed:
            raise RuntimeError(f"Failed to fetch running config: {task_result.exception}")

        running_config = task_result.result["config"]["running"]
        parse = CiscoConfParse(running_config.splitlines(), syntax='ios')

        results = super().verify_config_applied(configuration)

        # IFACE / SUBIFACE CONFIG

        if "iface" in configuration:
            iface_name = configuration["iface"]
            if "subiface_num" in configuration:
                iface_name = f"{iface_name}.{configuration['subiface_num']}"
                intf_objs = parse.find_objects(rf'^interface\s+{re.escape(iface_name)}\b')
                results[f"iface {iface_name} present"] = bool(intf_objs)

            intf_objs = parse.find_objects(rf'^interface\s+{re.escape(iface_name)}\b')

            if intf_objs:
                p = intf_objs[0]

                if "description" in configuration:
                    desc = re.escape(configuration["description"])
                    results[f"iface {iface_name} description"] = p.has_child_with(rf'^\s*description\s+{desc}\s*$')

                if "ip_address" in configuration and "mask" in configuration:
                    ip = re.escape(str(configuration["ip_address"]))
                    m = re.escape(str(configuration["mask"]))
                    results[f"iface {iface_name} ip"] = p.has_child_with(rf'^\s*ip\s+address\s+{ip}\s+{m}\s*$')

                if configuration.get("is_up") is False:
                    results[f"iface {iface_name} shutdown"] = p.has_child_with(r'^\s*shutdown\s*$')
                elif configuration.get("is_up") is True:
                    # In the ciscos I am using, when the interface is not shutdown the word shutdown does not appear
                    results[f"iface {iface_name} no shutdown"] = not p.has_child_with(r'^\s*shutdown\s*$')

                # HSRP REDUNDANCY

                if ({"hsrp_virtual_ip", "hsrp_group", "hsrp_priority", "preempt"}
                        <= configuration.keys()):
                    grp = int(configuration["hsrp_group"])
                    vip = str(configuration["hsrp_virtual_ip"])

                    ip_ok = p.has_child_with(rf'^\s*standby\s+{grp}\s+ip\s+{re.escape(vip)}\s*$')
                    results[f"hsrp {iface_name}"] = ip_ok


        # DHCP

        if "helper_address" in configuration and "iface" in configuration:
            iface_name = configuration["iface"]
            intf_objs = parse.find_objects(rf'^interface\s+{re.escape(iface_name)}\b')
            if intf_objs:
                p = intf_objs[0]
                helper = re.escape(str(configuration["helper_address"]))
                results[f"dhcp helper address {iface_name}"] = p.has_child_with(rf'^\s*ip\s+helper-address\s+{helper}\s*$')
            else:
                results[f"dhcp_helper address {iface_name}"] = False

        if {"first_excluded_addr", "last_excluded_addr"} <= configuration.keys():
            a = str(configuration["first_excluded_addr"])
            b = str(configuration["last_excluded_addr"])
            if a == b:
                pat = rf'^ip\s+dhcp\s+excluded-address\s+{re.escape(a)}\s*$'
            else:
                pat = rf'^ip\s+dhcp\s+excluded-address\s+{re.escape(a)}\s+{re.escape(b)}\s*$'
            results["dhcp excluded addresses"] = bool(parse.find_lines(pat))

        if {"pool_name", "pool_network", "pool_gateway_ip"} <= configuration.keys():
            pool = str(configuration["pool_name"])
            net = configuration["pool_network"]
            if isinstance(net, str):
                net = IPv4Network(net, strict=False)
            nw = re.escape(net.network_address.exploded)
            nm = re.escape(net.netmask.exploded)
            gw = re.escape(str(configuration["pool_gateway_ip"]))
            dns = configuration.get("pool_dns_ip")

            pool_objs = parse.find_objects(rf'^ip\s+dhcp\s+pool\s+{re.escape(pool)}\s*$')
            pool_ok = False
            if pool_objs:
                p = pool_objs[0]
                net_ok = p.has_child_with(rf'^\s*network\s+{nw}\s+{nm}\s*$')
                gw_ok = p.has_child_with(rf'^\s*default-router\s+{gw}\s*$')
                if dns:
                    dns_ok = p.has_child_with(rf'^\s*dns-server\s+{re.escape(str(dns))}\s*$')
                else:
                    dns_ok = True
                pool_ok = net_ok and gw_ok and dns_ok

                results[f"dhcp pool {pool} network"] = net_ok
                results[f"dhcp pool {pool} gateway"] = gw_ok
                if dns:
                    results[f"dhcp_pool {pool} dns"] = dns_ok
            results["dhcp pool"] = pool_ok

        # STATIC ROUTING

        if {"dest_ip", "next_hop"} <= configuration.keys():
            dest = str(configuration["dest_ip"])
            nh = str(configuration["next_hop"])
            ad = configuration.get("admin_distance")

            net = IPv4Network(dest, strict=False)
            dip = net.network_address.exploded
            msk = net.netmask.exploded

            if ad is not None and ad != 1:
                pat = rf'^ip\s+route\s+{re.escape(dip)}\s+{re.escape(msk)}\s+{re.escape(nh)}\s+{int(ad)}\s*$'
            else:
                pat = rf'^ip\s+route\s+{re.escape(dip)}\s+{re.escape(msk)}\s+{re.escape(nh)}\s*$'
            key = f"static route {dip} {msk} {nh}" + (f" {ad}" if ad is not None else "")
            results[key] = bool(parse.find_lines(pat))

        # OSPF

        if "process_id" in configuration:
            pid = int(configuration["process_id"])
            ospf_objs = parse.find_objects(rf'^router\s+ospf\s+{pid}\b')
            results[f"ospf {pid} present"] = bool(ospf_objs)

            if ospf_objs:
                p_router = ospf_objs[0]

                if "router_id" in configuration:
                    rid = re.escape(str(configuration["router_id"]))
                    results[f"ospf {pid} router_id"] = p_router.has_child_with(rf'^\s*router-id\s+{rid}\s*$')

                if "reference-bandwidth" in configuration:
                    rbw = int(configuration["reference-bandwidth"])
                    results[f"ospf {pid} reference bandwidth"] = p_router.has_child_with(
                        rf'^\s*auto-cost\s+reference-bandwidth\s+{rbw}\s*$'
                    )

                if {"network_ip", "network_area"} <= configuration.keys():
                    network = IPv4Network(configuration['network_ip'])
                    nip = network.network_address.exploded
                    wc = network.hostmask.exploded

                    area = re.escape(str(configuration["network_area"]))
                    results[f"ospf {pid} network {nip}"] = p_router.has_child_with(
                        rf'^\s*network\s+{nip}\s+{wc}\s+area\s+{area}\s*$'
                    )

                if configuration.get("is_redistribute") is True:
                    pat = rf'^\s*redistribute\s+static\s+subnets\s*$'
                    results[f"ospf {pid} redistribute static subnets"] = p_router.has_child_with(pat)


        if "iface_list" in configuration:
            passive_ifaces = []
            for item in configuration['iface_list']:
                name = item['name']
                intf_objs = parse.find_objects(rf'^interface\s+{re.escape(name)}\b')
                if not intf_objs:
                    continue
                p_if = intf_objs[0]

                if "hello_interval" in configuration[name]:
                    hi = int(configuration[name]["hello_interval"])
                    results[f"ospf {name} hello"] = p_if.has_child_with(
                        rf'^\s*ip\s+ospf\s+hello-interval\s+{hi}\s*$'
                    )
                if "dead_interval" in configuration[name]:
                    di = int(configuration[name]["dead_interval"])
                    results[f"ospf {name} dead"] = p_if.has_child_with(
                        rf'^\s*ip\s+ospf\s+dead-interval\s+{di}\s*$'
                    )
                if "priority" in configuration[name]:
                    pr = int(configuration[name]["priority"])
                    results[f"ospf {name}_priority"] = p_if.has_child_with(
                        rf'^\s*ip\s+ospf\s+priority\s+{pr}\s*$'
                    )
                if "cost" in configuration[name]:
                    cost = int(configuration[name]["cost"])
                    results[f"ospf {name} cost"] = p_if.has_child_with(
                        rf'^\s*ip\s+ospf\s+cost\s+{cost}\s*$'
                    )
                if configuration[name].get("is_pint_to_point") is True:  # matches your config() key
                    results[f"ospf {name} p2p"] = p_if.has_child_with(
                        r'^\s*ip\s+ospf\s+network\s+point-to-point\s*$'
                    )

                if "is_passive" in configuration[name]:
                    passive_ifaces.append(name)

            if len(passive_ifaces) > 0:
                pid = int(configuration["process_id"])
                ospf_objs = parse.find_objects(rf'^router\s+ospf\s+{pid}\b')
                p_router = ospf_objs[0]
                for pif in passive_ifaces:
                    results[f"ospf {pid} passive {pif}"] = p_router.has_child_with(
                        rf'^\s*passive-interface\s+{re.escape(pif)}\s*$'
                    )

        return results

