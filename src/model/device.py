
from typing import List, cast
from ipaddress import IPv4Address
from nornir import InitNornir
from nornir_netmiko.tasks import netmiko_save_config
from nornir_napalm.plugins.tasks import napalm_get
from ciscoconfparse import CiscoConfParse

from model.security import Security

class Device:
    def __init__(self, hostname: str, mgmt_ip: IPv4Address, mgmt_iface: str, security: dict = None,
                 users: List[dict] = None, banner: str = None, ip_domain_lookup: bool = False):
        self.security = Security(security["is_encrypted"], security["console_by_password"],
                                 security['enable_by_password'], security["protocols"])
        self.hostname = hostname
        self.mgmt_ip = mgmt_ip
        self.mgmt_iface = mgmt_iface
        self.users = users
        self.banner = banner
        self.ip_domain_lookup = ip_domain_lookup


    def update(self, config_info: dict) -> None:

        if config_info['device_name']: self.hostname = config_info['device_name']
        if config_info['ip_domain_lookup']: self.ip_domain_lookup = config_info['ip_domain_lookup']
        if config_info['username']:
            self.users.append({'username': config_info['username'], 'privilege': config_info['privilege']})
        if config_info['username_delete']:
            for user in self.users:
                if user['username'] == config_info['username_delete']:
                    self.users.pop(user)
                    break
        if config_info['banner_motd']: self.banner = config_info['banner_motd']

        self.security.update(config_info)


    def get_device_info(self) -> dict:
        device_info = dict()
        device_info["device_name"] = self.hostname
        device_info["mgmt_iface"] = self.mgmt_iface
        device_info["mgmt_ip"] = self.mgmt_ip

        device_info["security"] = self.security.get_info()
        device_info["users"] = self.users
        device_info["banner"] = self.banner
        device_info["ip_domain_lookup"] = self.ip_domain_lookup

        return device_info


    def verify_config_applied(self, configuration: dict) -> dict:
        """
        Verifies whether the intended configuration has been applied to the device.

        Args:
            configuration (dict): The same dict passed to `config()`.

        Returns:
            dict: A dictionary with verification results.
        """
        nr = InitNornir(config_file="config/config.yaml")
        target = nr.filter(name=self.hostname)

        # Fetch running config
        result = target.run(task=napalm_get, getters=["config"])
        task_result = result[self.hostname]

        if task_result.failed:
            raise RuntimeError(f"Failed to fetch running config: {task_result.exception}")

        running_config = task_result.result["config"]["running"]
        parse = CiscoConfParse(running_config.splitlines())

        results = {}

        # BASIC CONFIG
        if "device_name" in configuration:
            hostname_line = parse.find_lines(r"^hostname ")[0] if parse.find_lines(r"^hostname ") else ""
            results["hostname"] = hostname_line == f"hostname {configuration['device_name']}"

        if "ip_domain_lookup" in configuration:
            has_no_lookup = bool(parse.find_lines(r"^no ip domain-lookup"))
            results["ip_domain_lookup"] = not has_no_lookup if configuration["ip_domain_lookup"] else has_no_lookup

        if "banner_motd" in configuration:
            banner_line = parse.find_lines(r"^banner motd")[0] if parse.find_lines(r"^banner motd") else ""
            expected_banner = configuration["banner_motd"].replace("^", "")
            results["banner_motd"] = expected_banner in banner_line

        if "username" in configuration:
            lines = parse.find_lines(rf"^username {configuration['username']} ")
            results[f"username_{configuration['username']}"] = len(lines) > 0

        if "username_delete" in configuration:
            lines = parse.find_lines(rf"^username {configuration['username_delete']} ")
            results[f"removed_user_{configuration['username_delete']}"] = len(lines) == 0

        # SECURITY CONFIG
        if "enable_passwd" in configuration:
            enable_line = parse.find_lines(r"^enable secret")[0] if parse.find_lines(r"^enable secret") else ""
            results["enable_secret"] = bool(enable_line)

        if configuration.get("password_encryption"):
            results["password_encryption"] = bool(parse.find_lines(r"^service password-encryption"))

        if "console_access" in configuration:
            console_block = parse.find_parents_w_child("line console 0", "login")
            if configuration["console_access"] == "local_database":
                results["console_access"] = any(
                    "login local" in child.text for p in console_block for child in p.children)
            elif configuration["console_access"] == "password":
                results["console_access"] = any("password" in child.text for p in console_block for child in p.children)

        if "vty_protocols" in configuration:
            vty_lines = parse.find_parents_w_child("line vty", "transport input")
            if configuration["vty_protocols"] == "ssh":
                results["vty_protocols"] = any(
                    "transport input ssh" in child.text for p in vty_lines for child in p.children)
            elif configuration["vty_protocols"] == "both":
                results["vty_protocols"] = any(
                    "transport input all" in child.text for p in vty_lines for child in p.children)

        return results

    def config(self, configuration: dict) -> list:

        nr = InitNornir(config_file="config/config.yaml")
        target = nr.filter(name=self.hostname)

        config_lines = []

        # BASIC CONFIG
        if "device_name" in configuration:
            config_lines.append(f"hostname {configuration['device_name']}")

        if "ip_domain_lookup" in configuration:
            if configuration["ip_domain_lookup"]:
                config_lines.append("ip domain-lookup")
            else:
                config_lines.append("no ip domain-lookup")

        if "username" in configuration:
            config_lines.append(
                f"username {configuration['username']} privilege {configuration.get('privilege', 1)} "
                f"secret {configuration['password']}")

        if "username_delete" in configuration:
                config_lines.append(f"no username {configuration['username_delete']}")

        if "banner_motd" in configuration:
            banner = configuration["banner_motd"].replace("^", "")
            config_lines.append(f"banner motd ^{banner}^")

        # SECURITY CONFIG
        if configuration.get("password_encryption"):
            config_lines.append("service password-encryption")

        if configuration.get("console_access") == "local_database":
            config_lines.extend([
                "line console 0",
                "login local"
            ])
        elif configuration.get("console_access") == "password":
            config_lines.extend([
                "line console 0",
                f"password {configuration['console_password']}",
                "login"
            ])

        if configuration.get("vty_protocols") == "both":
            config_lines.extend([
                "line vty 0 4",
                "transport input all"
            ])
        elif configuration.get("vty_protocols") == "ssh":
            config_lines.extend([
                "line vty 0 4",
                "transport input ssh"
            ])


        if "enable_passwd" in configuration:
            config_lines.append(f"enable secret {configuration['enable_passwd']}")

        if not config_lines:
            print("No configuration to apply.")
            return config_lines

        return config_lines

    def save_config(self) -> bool:
        nr = InitNornir(config_file="config/config.yaml")
        target = nr.filter(name=self.hostname)

        res = target.run(task=netmiko_save_config)
        host = list(target.inventory.hosts.keys())[0]
        if res[host].failed:
            return False
        else:
            return True