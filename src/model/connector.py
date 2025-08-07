from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get
from ciscoconfparse import CiscoConfParse
from loguru import logger
from netmiko import ConnectHandler

class Connector:
    def __init__(self):
        logger.remove()
      
    def get_device_info(self, connect_info: dict) -> dict:
        """
        Retrieves the running configuration of the device matching the given IP address.
        Params:
            connect_info (dict): Dictionary with connection data, must include 'ip'.
        Returns:
            dict: Dictionary with the running configuration, or empty if not found.
        """

        device_info = dict()

        nr = InitNornir(config_file="config/config.yaml")

        target = nr.filter(name=connect_info["name"])

        result = target.run(task=napalm_get, getters=["config"])
        hostname = list(target.inventory.hosts.keys())[0]

        task_result = result[hostname]

        if task_result.failed:
            raise RuntimeError(f"NAPALM task failed: {task_result.exception}")

        running_config = result[hostname].result["config"]["running"]
        parse = CiscoConfParse(running_config.splitlines(), syntax='ios')

        # SECURITY
        service_password_encryption = False
        for p in parse.find_objects('^service password-encryption'):
            if p.text == 'service password-encryption':
                service_password_encryption = True
                break

        console_password = False
        for p in parse.find_objects(r'^line con'):
            if p.text.startswith('line con') and p.has_child_with(r'password'):
                console_password = True
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

        transport_input = []
        for p in parse.find_objects(r'^line vty'):
            if p.re_search_children(r'transport input'):
                proto = p.re_match_iter_typed(r'transport input (\S+)', default=None)
                transport_input.append(proto)

        protocols = []
        for proto in transport_input:
            if proto and proto not in protocols:
                protocols.append(proto)

        device_info["security"] = {
            "is_encrypted": service_password_encryption,
            "console_by_password": console_password,
            "enable_by_password": has_enable_password,
            "vty_by_password": vty_password,
            "protocols": protocols
        }

        # INTERFACES
        interfaces = []
        for intf in parse.find_objects(r"^interface "):
            ip_line = intf.re_search_children(r'ip address')
            ip_address = None
            if ip_line:
                ip_address = ip_line[0].re_match_iter_typed(r'ip address (\S+ \S+)', default=None)

            ospf_line = intf.re_search_children(r'ip ospf')
            ospf = bool(ospf_line)

            hsrp_line = intf.re_search_children(r'standby \d+ ip')
            l3_redundancy = bool(hsrp_line)

            is_up = True
            for c in intf.children:
                if 'shutdown' in c.text:
                    is_up = False
                    break

            description = ""
            for c in intf.children:
                if 'description' in c.text:
                    description = c.re_match_iter_typed(r'description (.+)', default="")
                    break

            interfaces.append({
                "name": intf.text.split()[-1],
                "is_up": is_up,
                "description": description,
                "ip_address": ip_address,
                "ospf": ospf,
                "l3_redundancy": l3_redundancy
            })

        device_info["interfaces"] = interfaces

        # USERS
        users = []
        for user in parse.find_objects(r'^username '):
            username = user.re_match_iter_typed(r'^username (\S+)', default=None)
            password = user.re_match_iter_typed(r'password (\d+ )?(\S+)', result_type=str, default=None)
            users.append({"username": username, "password": password})
        device_info["users"] = users

        # BANNER
        banner_lines = parse.find_lines(r'^banner motd')
        banner = banner_lines[0] if banner_lines else None
        device_info["banner"] = banner

        # DHCP
        pools = []
        excluded_addresses = []
        helper_addresses = []

        for pool in parse.find_objects(r'^ip dhcp pool'):
            name = pool.re_match_iter_typed(r'^ip dhcp pool (\S+)', default=None)

            network = None
            for c in pool.children:
                if 'network' in c.text:
                    network = c.re_match_iter_typed(r'network (\S+ \S+)', default=None)
                    break

            default_router = None
            for c in pool.children:
                if 'default-router' in c.text:
                    default_router = c.re_match_iter_typed(r'default-router (\S+)', default=None)
                    break

            pools.append({
                "name": name,
                "network": network,
                "default_router": default_router
            })

        for ex in parse.find_lines(r'^ip dhcp excluded-address'):
            parts = ex.split()
            if len(parts) == 4:
                excluded_addresses.append({"start": parts[3], "end": parts[3]})
            elif len(parts) == 5:
                excluded_addresses.append({"start": parts[3], "end": parts[4]})

        for intf in parse.find_objects(r"^interface "):
            helper_lines = intf.re_search_children(r'ip helper-address')
            for h in helper_lines:
                ip = h.re_match_iter_typed(r'ip helper-address (\S+)', default=None)
                if ip:
                    helper_addresses.append(ip)

        device_info["dhcp"] = {
            "pools": pools,
            "excluded_address": excluded_addresses,
            "helper_address": helper_addresses
        }

        # ROUTING
        ospf_processes = []
        static_routes = []
        for ospf in parse.find_objects(r'^router ospf'):
            process_id = ospf.re_match_iter_typed(r'^router ospf (\d+)', result_type=int, default=1)
            networks = []
            for child in ospf.children:
                if 'network' in child.text:
                    net = child.re_match_iter_typed(r'network (\S+ \S+) area (\d+)', default=None)
                    if net:
                        networks.append({"network": net[0], "area": int(net[1])})
            ospf_processes.append({
                "process_id": process_id,
                "networks": networks
            })

        for line in parse.find_lines(r'^ip route'):
            parts = line.split()
            if len(parts) >= 4:
                static_routes.append({
                    "destination": f"{parts[2]} {parts[3]}",
                    "next_hop": parts[4] if len(parts) > 4 else None
                })

        device_info["routing_process"] = {
            "ospf_processes": ospf_processes,
            "static_routes": static_routes
        }

        return device_info

    def push_config_with_netmiko(self, host: str, access_data: dict, config_lines: list):
        device = {
            "device_type": "cisco_ios",
            "host": host,
            "username": access_data['username'],
            "password": access_data['password']
        }

        conn = ConnectHandler(**device)
        output = conn.send_config_set(config_lines)

        conn.disconnect()
        return output