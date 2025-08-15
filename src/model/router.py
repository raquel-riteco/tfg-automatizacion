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
                config_lines += [f"encapsulation dot1Q {sub}"]

            else:
                config_lines += [f"interface {iface}"]

            if "iface_desc" in configuration:
                config_lines.append(f"description {configuration['iface_desc']}")

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
        target = nr.filter(name=self.hostname)

        result = target.run(task=napalm_get, getters=["config"])
        task_result = result[self.hostname]
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

                if "iface_desc" in configuration:
                    desc = re.escape(configuration["iface_desc"])
                    results[f"iface {iface_name} description"] = p.has_child_with(rf'^\s*description\s+{desc}\s*$')

                if "ip_addr" in configuration and "mask" in configuration:
                    ip = re.escape(str(configuration["ip_addr"]))
                    m = re.escape(str(configuration["mask"]))
                    results[f"iface {iface_name} ip"] = p.has_child_with(rf'^\s*ip\s+address\s+{ip}\s+{m}\s*$')

                if configuration.get("iface_shutdown") is True:
                    results[f"iface {iface_name} shutdown"] = p.has_child_with(r'^\s*shutdown\s*$')
                elif configuration.get("iface_shutdown") is False:
                    # In the ciscos I am using, when the interface is not shutdown the word shutdown does not appear
                    results[f"iface {iface_name} no shutdown"] = not p.has_child_with(r'^\s*shutdown\s*$')

        # HSRP REDUNDANCY

        if ({"hsrp_virtual_ip", "iface_list", "hsrp_group", "hsrp_priority", "hsrp_preempt"}
                <= configuration.keys()):
            grp = int(configuration["hsrp_group"])
            vip = str(configuration["hsrp_virtual_ip"])
            prio = int(configuration["hsrp_priority"])

            preempt = configuration.get("hsrp_preempt")
            if preempt is None:
                preempt = configuration.get("preempt")

            per_iface_ok = []
            for iface in configuration["iface_list"]:
                intf_objs = parse.find_objects(rf'^interface\s+{re.escape(str(iface))}\b')
                ok = False
                if intf_objs:
                    p = intf_objs[0]
                    ip_ok = p.has_child_with(rf'^\s*standby\s+{grp}\s+ip\s+{re.escape(vip)}\s*$')
                    pr_ok = p.has_child_with(rf'^\s*standby\s+{grp}\s+priority\s+{prio}\s*$')
                    if preempt is True:
                        prpt_ok = p.has_child_with(rf'^\s*standby\s+{grp}\s+preempt\s*$')
                    elif preempt is False:
                        prpt_ok = p.has_child_with(rf'^\s*no\s+standby\s+{grp}\s+preempt\s*$')
                    else:
                        prpt_ok = True  # not specified; don't fail on it
                    ok = ip_ok and pr_ok and prpt_ok

                results[f"hsrp {iface}"] = ok
                per_iface_ok.append(ok)

            results["hsrp all"] = all(per_iface_ok) if per_iface_ok else False

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

                results[f"dhcp pool {pool}_network"] = net_ok
                results[f"dhcp pool {pool}_gateway"] = gw_ok
                if dns:
                    results[f"dhcp_pool {pool} dns"] = dns_ok
            results["dhcp_pool"] = pool_ok

        # STATIC ROUTING

        if {"dest_ip", "next_hop"} <= configuration.keys():
            dest = str(configuration["dest_ip"])
            nh = str(configuration["next_hop"])
            ad = configuration.get("admin_distance")

            if "/" in dest:
                net = IPv4Network(dest, strict=False)
                dip = net.network_address.exploded
                msk = net.netmask.exploded
            else:
                parts = dest.split()
                if len(parts) == 2:
                    dip, msk = parts
                else:
                    raise ValueError("dest_ip must be 'A.B.C.D/M' or 'A.B.C.D MASK'")

            if ad is not None:
                pat = rf'^ip\s+route\s+{re.escape(dip)}\s+{re.escape(msk)}\s+{re.escape(nh)}\s+{int(ad)}\s*$'
            else:
                pat = rf'^ip\s+route\s+{re.escape(dip)}\s+{re.escape(msk)}\s+{re.escape(nh)}\s*$'
            key = f"static_route_{dip}_{msk}_{nh}" + (f"_{ad}" if ad is not None else "")
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

                if {"network_ip", "network_wildcard", "network_area"} <= configuration.keys():
                    nip = re.escape(str(configuration["network_ip"]))
                    wc = re.escape(str(configuration["network_wildcard"]))
                    area = re.escape(str(configuration["network_area"]))
                    results[f"ospf {pid} network"] = p_router.has_child_with(
                        rf'^\s*network\s+{nip}\s+{wc}\s+area\s+{area}\s*$'
                    )

                if configuration.get("is_redistribute") is True:
                    what = str(configuration.get("redistribute_what", "connected"))
                    if what in ("connected", "static", "rip", "eigrp", "bgp"):
                        pat = rf'^\s*redistribute\s+{re.escape(what)}\s+subnets\s*$'
                    else:
                        pat = rf'^\s*redistribute\s+{re.escape(what)}\s*$'
                    results[f"ospf {pid} redistribute {what}"] = p_router.has_child_with(pat)


            iface_items = configuration.get("iface_list")
            if isinstance(iface_items, list) and iface_items:

                norm = []
                for item in iface_items:
                    if isinstance(item, dict):
                        name = item.get("iface_name") or item.get("name")
                        ospf = item.get("ospf", {})
                        if name:
                            norm.append({"name": name, "ospf": ospf})
                    else:
                        norm.append({"name": str(item), "ospf": {}})

                for entry in norm:
                    name = entry["name"]
                    ospf = entry["ospf"]
                    intf_objs = parse.find_objects(rf'^interface\s+{re.escape(name)}\b')
                    if not intf_objs:
                        continue
                    p_if = intf_objs[0]

                    if "hello_interval" in ospf:
                        hi = int(ospf["hello_interval"])
                        results[f"ospf {pid} {name} hello"] = p_if.has_child_with(
                            rf'^\s*ip\s+ospf\s+hello-interval\s+{hi}\s*$'
                        )
                    if "dead_interval" in ospf:
                        di = int(ospf["dead_interval"])
                        results[f"ospf {pid} {name} dead"] = p_if.has_child_with(
                            rf'^\s*ip\s+ospf\s+dead-interval\s+{di}\s*$'
                        )
                    if "priority" in ospf:
                        pr = int(ospf["priority"])
                        results[f"ospf {pid} {name}_priority"] = p_if.has_child_with(
                            rf'^\s*ip\s+ospf\s+priority\s+{pr}\s*$'
                        )
                    if "cost" in ospf:
                        cost = int(ospf["cost"])
                        results[f"ospf {pid} {name} cost"] = p_if.has_child_with(
                            rf'^\s*ip\s+ospf\s+cost\s+{cost}\s*$'
                        )
                    if ospf.get("is_pint_to_point") is True:  # matches your config() key
                        results[f"ospf {pid} {name} p2p"] = p_if.has_child_with(
                            r'^\s*ip\s+ospf\s+network\s+point-to-point\s*$'
                        )

                passive_ifaces = [
                    e["name"]
                    for e in norm
                    if isinstance(e.get("ospf"), dict) and e["ospf"].get("is_passive") is True
                ]
                if passive_ifaces and ospf_objs:
                    p_router = ospf_objs[0]
                    for pif in passive_ifaces:
                        results[f"ospf {pid} passive {pif}"] = p_router.has_child_with(
                            rf'^\s*passive-interface\s+{re.escape(pif)}\s*$'
                        )

        return results