from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get
from ciscoconfparse import CiscoConfParse
from loguru import logger
from netmiko import ConnectHandler
import re
from ipaddress import IPv4Address, IPv4Network

class Connector:
    def __init__(self):
        logger.remove()
      
    def get_device_info(self, connect_info: dict) -> dict:
        """
        Retrieves the running configuration of the device matching the given IP address.
        Params:
            connect_info (dict): Dictionary with connection data, must include 'device_name'.
        Returns:
            dict: Dictionary with the running configuration, or empty if not found.
        """

        device_info = dict()

        nr = InitNornir(config_file="config/config.yaml")

        target = nr.filter(name=connect_info["device_name"])

        result = target.run(task=napalm_get, getters=["config"])
        hostname = list(target.inventory.hosts.keys())[0]

        task_result = result[hostname]

        if task_result.failed:
            raise RuntimeError(f"NAPALM task failed: {task_result.exception}")

        running_config = result[hostname].result["config"]["running"]
        parse = CiscoConfParse(running_config.splitlines(), syntax='ios')

        # BASIC CONFIG
        hostname_line = parse.find_lines(r"^hostname ")
        device_info['device_name'] = None
        if hostname_line:
            device_info['device_name'] = hostname_line[0].split(maxsplit=1)[1].strip()

        no_lookup = bool(parse.find_lines(r"^no ip domain-lookup"))
        yes_lookup = bool(parse.find_lines(r"^ip domain-lookup"))
        if no_lookup:
            device_info['ip_domain_lookup'] = False
        elif yes_lookup:
            device_info['ip_domain_lookup'] = True
        else:
            # IOS default is typically disabled
            device_info['ip_domain_lookup'] = False

        device_info['banner_motd'] = None
        banner_lines = parse.find_lines(r"^banner motd")
        if banner_lines:
            raw = banner_lines[0]
            m = re.search(r"^banner\s+motd\s+(.)(.*)\1$", raw)
            device_info['banner_motd'] = m.group(2) if m else raw  # fallback to raw line

        device_info['users'] = []

        for user in parse.find_objects(r'^username\s+\S+'):
            username = user.re_match_iter_typed(r'^username\s+(\S+)', default=None)
            # privilege (default 1 if not present)
            privilege = user.re_match_iter_typed(r'\bprivilege\s+(\d+)', result_type=int, default=1)

            device_info['users'].append({
                "username": username,
                "privilege": privilege
            })

        # SECURITY
        service_password_encryption = False
        for p in parse.find_objects('^service password-encryption'):
            if p.text == 'service password-encryption':
                service_password_encryption = True
                break

        console_access = None
        for p in parse.find_objects(r'^line con'):
            if p.has_child_with(r'^\s*login\s+local\b'):
                console_access = "local_database"
                break
            if p.has_child_with(r'^\s*login\b') and p.has_child_with(r'^\s*password(?:\s+\d+)?\s+\S+'):
                console_access = "password"
                break

        has_enable_password = False
        for line in parse.find_lines(r'^enable (password|secret)'):
            if line.startswith("enable password") or line.startswith("enable secret"):
                has_enable_password = True
                break

        vty_password = False
        for p in parse.find_objects(r'^line vty'):
            if p.text.startswith('line vty') and p.has_child_with(r'password'):
                vty_password = True
                break

        vty_protocols = []
        for p in parse.find_objects(r'^line vty'):
            if p.re_search_children(r'transport input'):
                proto = p.re_match_iter_typed(r'transport input (\S+)', default=None)
                if proto not in vty_protocols:
                    vty_protocols.append(proto)

        device_info["security"] = {
            "is_encrypted": service_password_encryption,
            "console_access": console_access,
            "enable_by_password": has_enable_password,
            "vty_by_password": vty_password,
            "vty_protocols": vty_protocols
        }

        if connect_info['device_type'] == 'R':
            # INTERFACES
            interfaces = []

            passive_default = False
            passive_set = set()
            no_passive_set = set()
            for ospf_proc in parse.find_objects(r'^router ospf'):
                for ch in ospf_proc.children:
                    if ch.text.strip() == 'passive-interface default':
                        passive_default = True
                    m = ch.re_match_iter_typed(r'^passive-interface\s+(\S+)', default=None)
                    if m:
                        passive_set.add(m)
                    m = ch.re_match_iter_typed(r'^no passive-interface\s+(\S+)', default=None)
                    if m:
                        no_passive_set.add(m)

            for intf in parse.find_objects(r"^interface "):
                ip_line = intf.re_search_children(r'ip address')
                ip_address = None
                if ip_line:
                    raw_ip = ip_line[0].re_match_iter_typed(r'ip address (\S+ \S+)', default=None)
                    if raw_ip == 'None':
                        ip_address = None
                        netmask = None
                    else:
                        ip_address = raw_ip.split()[0]
                        netmask = raw_ip.split()[1]
                        ip_address = IPv4Address(ip_address)
                        netmask = IPv4Address(netmask)

                is_up = True
                for c in intf.children:
                    if 'shutdown' in c.text:
                        is_up = False
                        break

                description = None
                for c in intf.children:
                    if 'description' in c.text:
                        description = c.re_match_iter_typed(r'description (.+)', default="")
                        break

                name = intf.text.split()[-1]

                # OSPF
                ospf_hello = intf.re_match_iter_typed(r'ip ospf hello-interval (\d+)', default=None)
                if ospf_hello == 'None':
                    ospf_hello = None
                else:
                    ospf_hello = int(ospf_hello)
                ospf_dead = intf.re_match_iter_typed(r'ip ospf dead-interval (\d+)', default=None)
                if ospf_dead == 'None':
                    ospf_dead = None
                else:
                    ospf_dead = int(ospf_dead)
                ospf_prio = intf.re_match_iter_typed(r'ip ospf priority (\d+)', default=None)
                if ospf_prio == 'None':
                    ospf_prio = None
                else:
                    ospf_prio = int(ospf_prio)
                ospf_cost = intf.re_match_iter_typed(r'ip ospf cost (\d+)', default=None)
                if ospf_cost == 'None':
                    ospf_cost = None
                else:
                    ospf_cost = int(ospf_cost)
                ospf_ptp = intf.re_search_children(r'ip ospf network point-to-point')
                ospf_ptp = bool(ospf_ptp)

                if name in no_passive_set:
                    ospf_passive = False
                elif name in passive_set:
                    ospf_passive = True
                else:
                    ospf_passive = passive_default

                ospf_dict = {
                    "hello_interval": ospf_hello,
                    "dead_interval": ospf_dead,
                    "is_passive": ospf_passive,
                    "priority": ospf_prio,
                    "cost": ospf_cost,
                    "is_pint_to_point": ospf_ptp,
                }

                # HSRP
                hsrp_vip = None
                hsrp_prio = None
                hsrp_pre = None
                hsrp_group = intf.re_match_iter_typed(r'standby\s+(\d+)\s+ip\s+\S+', default=None)
                if hsrp_group == 'None':
                    hsrp_group = None
                else:
                    hsrp_group = int(hsrp_group)
                    hsrp_vip_s = intf.re_match_iter_typed(r'standby\s+\d+\s+ip\s+(\S+)', default=None)
                    if hsrp_vip_s == 'None':
                        hsrp_vip_s = None
                    hsrp_vip = IPv4Address(hsrp_vip_s) if hsrp_vip_s else None
                    hsrp_prio = intf.re_match_iter_typed(rf'standby\s+{hsrp_group}\s+priority\s+(\d+)',
                                                         default=None)
                    if hsrp_prio is not None:
                        hsrp_prio = int(hsrp_prio)
                    hsrp_pre = bool(
                        intf.re_search_children(rf'standby\s+{hsrp_group}\s+preempt'))

                l3_redundancy = {
                    "hsrp_group": hsrp_group,
                    "hsrp_virtual_ip": hsrp_vip,
                    "hsrp_priority": hsrp_prio,
                    "preempt": hsrp_pre,
                }

                helper_address = None
                helper_lines = intf.re_search_children(r'ip helper-address')
                for h in helper_lines:
                    ip = h.re_match_iter_typed(r'ip helper-address (\S+)', default=None)
                    if ip:
                        if ip == 'None':
                            ip = None
                        helper_address = IPv4Address(ip)

                interfaces.append({
                    "name": intf.text.split()[-1],
                    "is_up": is_up,
                    "description": description,
                    "ip_address": ip_address,
                    "netmask": netmask,
                    "ospf": ospf_dict,
                    "l3_redundancy": l3_redundancy,
                    "helper_address": helper_address
                })

            device_info["interfaces"] = interfaces

            # DHCP
            pools = []
            excluded_addresses = []

            for pool in parse.find_objects(r'^ip dhcp pool'):
                name = pool.re_match_iter_typed(r'^ip dhcp pool (\S+)', default=None)

                network = None
                for c in pool.children:
                    if 'network' in c.text:
                        network = c.re_match_iter_typed(r'network (\S+ \S+)', default=None)
                        if network == 'None':
                            network = None
                        if network is not None:
                            network = IPv4Network(network)
                        break

                default_router = None
                for c in pool.children:
                    if 'default-router' in c.text:
                        default_router = c.re_match_iter_typed(r'default-router (\S+)', default=None)
                        if default_router == 'None':
                            default_router = None
                        if default_router is not None:
                            default_router = IPv4Address(default_router)
                        break
                pools.append({
                    "name": name,
                    "network": network,
                    "default_router": default_router
                })

            for ex in parse.find_lines(r'^ip dhcp excluded-address'):
                parts = ex.split()
                if len(parts) == 4:
                    excluded_addresses.append({"start": IPv4Address(parts[3]), "end": IPv4Address(parts[3])})
                elif len(parts) == 5:
                    excluded_addresses.append({"start": IPv4Address(parts[3]), "end": IPv4Address(parts[4])})

            device_info["dhcp"] = {
                "pools": pools,
                "excluded_address": excluded_addresses
            }

            # ROUTING
            ospf_processes = []
            static_routes = []
            for ospf in parse.find_objects(r'^router ospf'):
                process_id = ospf.re_match_iter_typed(r'^router ospf (\d+)', result_type=int, default=1)
                networks = []
                for child in ospf.children:
                    if 'network' in child.text:
                        net = child.text.split(' ')
                        if net:
                            networks.append({"network": IPv4Network(f'{net[2]}/{net[3]}'), "network_area": int(net[5])})

                router_id = next(
                    (c.re_match_iter_typed(r'^\s*router-id\s+(\S+)', default=None) for c in ospf.children
                     if 'router-id' in c.text),
                    None
                )

                # Reference bandwidth (in Mbps)
                reference_bw = next(
                    (c.re_match_iter_typed(r'^\s*auto-cost\s+reference-bandwidth\s+(\d+)',
                                           result_type=int, default=None) for c in ospf.children
                    if 'reference-bandwidth' in c.text),
                    None
                )

                redistribute_static_subnets = any(
                    re.search(r'^\s*redistribute\s+static(?:\s+\S+)*\s+subnets\b', c.text)
                    for c in ospf.children
                )

                ospf_processes.append({
                    "process_id": process_id,
                    "networks": networks,
                    "bw_cost": reference_bw,
                    "redistribute": redistribute_static_subnets,
                    "router_id": router_id
                })

            for line in parse.find_lines(r'^ip route'):
                parts = line.split()
                if len(parts) >= 4:
                    static_routes.append({
                        "destination": IPv4Network(f"{parts[2]}/{parts[3]}"),
                        "next_hop": IPv4Address(parts[4]),
                        "admin_dist": parts[5] if len(parts) > 5 else 1
                    })

            device_info["routing_process"] = {
                "ospf_processes": ospf_processes,
                "static_routes": static_routes
            }

        return device_info

    def push_config_with_netmiko(self, host: str, access_data: dict, config_lines: list) -> str:
        device = {
            "device_type": "cisco_ios",
            "host": host,
            "username": access_data['username'],
            "password": access_data['password']
        }

        conn = ConnectHandler(**device)

        output_chunks = []

        conn.config_mode()

        for cmd in config_lines:
            # Deleting a user can trigger "Do you want to continue? [confirm]"
            if re.search(r"^\s*no\s+username\s+\S+", cmd, flags=re.I):
                out = conn.send_command_timing(
                    cmd,
                    read_timeout=30,
                    strip_prompt=False,
                    strip_command=False,
                )
                if re.search(r"\[confirm\]", out, flags=re.I):
                    out += conn.send_command_timing(
                        "\n",
                        read_timeout=30,
                        strip_prompt=False,
                        strip_command=False,
                    )
                output_chunks.append(out)
            else:
                # Normal config commands
                out = conn.send_config_set(
                    [cmd],
                    exit_config_mode=False,
                    cmd_verify=False,
                    read_timeout=30,
                )
                output_chunks.append(out)

        if conn.check_config_mode():
            conn.exit_config_mode()

        conn.disconnect()

        return "\n".join(output_chunks)