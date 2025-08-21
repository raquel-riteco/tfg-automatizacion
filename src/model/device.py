from typing import List
from ipaddress import IPv4Address
from nornir import InitNornir
from nornir_netmiko.tasks import netmiko_save_config
from nornir_napalm.plugins.tasks import napalm_get
from ciscoconfparse import CiscoConfParse

from model.security import Security
from model.interface import normalize_iface


class Device:
    """
    Represents a generic network device with basic configuration and verification capabilities.

    This class provides an abstraction to apply, verify, and retrieve configuration for a device,
    specifically focusing on basic settings, user management, banner, security parameters, and VTY settings.
    """
    def __init__(self, device_name: str, mgmt_ip: IPv4Address, mgmt_iface: str, security: dict = None,
                 users: List[dict] = None, banner: str = None, ip_domain_lookup: bool = False):
        """
        Initialize a Device instance with basic and security parameters.

        Args:
            device_name (str): Hostname of the device.
            mgmt_ip (IPv4Address): Management IP address.
            mgmt_iface (str): Management interface name.
            security (dict, optional): Security-related configuration.
            users (List[dict], optional): List of local user accounts.
            banner (str, optional): MOTD banner.
            ip_domain_lookup (bool): Whether IP domain-lookup is enabled.
        """
        self.security = Security(security["is_encrypted"], security["console_access"],
                                 security['enable_by_password'], security["vty_protocols"])
        self.device_name = device_name
        self.mgmt_ip = mgmt_ip
        self.mgmt_iface = normalize_iface(mgmt_iface)
        self.users = users
        self.banner = banner
        self.ip_domain_lookup = ip_domain_lookup


    def update(self, config_info: dict) -> None:
        """
        Updates the internal state of the device with new configuration values.

        Args:
            config_info (dict): Dictionary containing updated values to apply.
        """
        if 'device_name' in config_info: self.device_name = config_info['device_name']
        if 'ip_domain_lookup' in config_info: self.ip_domain_lookup = config_info['ip_domain_lookup']
        if 'username' in config_info:
            self.users.append({'username': config_info['username'], 'privilege': config_info['privilege']})
        if 'username_delete' in config_info:
            for user in self.users:
                if user['username'] == config_info['username_delete']:
                    self.users.remove(user)
                    break
        if 'banner_motd' in config_info: self.banner = config_info['banner_motd']

        self.security.update(config_info)


    def get_device_info(self) -> dict:
        """
        Returns a summary of the device's configuration and state.

        Returns:
            dict: A dictionary containing hostname, IP, interface, security, users, banner, etc.
        """
        device_info = dict()
        device_info["device_name"] = self.device_name
        device_info["mgmt_iface"] = self.mgmt_iface
        device_info["mgmt_ip"] = self.mgmt_ip.exploded

        # When config is empty
        # banner = None
        # user only has ssh user
        # ip_domain_lookup is False

        device_info["security"] = self.security.get_info()
        device_info["users"] = self.users
        device_info["banner"] = self.banner
        device_info["ip_domain_lookup"] = self.ip_domain_lookup

        return device_info

    def get_config(self) -> dict:
        """
        Returns the current intended configuration of the device (not the actual running config).

        Returns:
            dict: Configuration fields relevant for pushing to the device.
        """
        device_config = dict()

        security = self.security.get_config()
        if security is not None:
            device_config['security'] = security

        if len(self.users) > 1:
            device_config['users'] = self.users

        if self.banner is not None:
            device_config['banner'] = self.banner

        device_config['ip_domain_lookup'] = self.ip_domain_lookup

        return device_config


    def verify_config_applied(self, configuration: dict) -> dict:
        """
        Verifies whether the intended configuration has been applied to the device.

        Args:
            configuration (dict): The same dict passed to `config()`.

        Returns:
            dict: A dictionary with verification results.
        """
        nr = InitNornir(config_file="config/config.yaml")
        target = nr.filter(name=self.device_name)

        # Fetch running config
        result = target.run(task=napalm_get, getters=["config"])
        task_result = result[self.device_name]

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
            results[f"username {configuration['username']}"] = len(lines) > 0

        if "username_delete" in configuration:
            lines = parse.find_lines(rf"^username {configuration['username_delete']} ")
            results[f"removed user {configuration['username_delete']}"] = len(lines) == 0

        # SECURITY CONFIG
        if "enable_passwd" in configuration:
            enable_line = parse.find_lines(r"^enable secret")[0] if parse.find_lines(r"^enable secret") else ""
            results["enable_secret"] = bool(enable_line)

        if configuration.get("password_encryption"):
            results["password_encryption"] = bool(parse.find_lines(r"^service password-encryption"))

        if "console_access" in configuration:
            if configuration["console_access"] == "local_database":
                results["console_access"] = bool(
                    parse.find_objects_w_child(r'^line\s+con', r'^\s*login\s+local\b')
                )

            elif configuration["console_access"] == "password":
                parents = parse.find_objects_w_child(r'^line\s+con', r'^\s*password(?:\s+\d+)?\s+\S+')
                results["console_access"] = any(
                    p.has_child_with(r'^\s*login\b') and not p.has_child_with(r'^\s*login\s+local\b')
                    for p in parents
                )

        if "vty_protocols" in configuration:
            vty_blocks = parse.find_objects(r'^line\s+vty\b')
            if len(configuration["vty_protocols"]) == 1:
                results["vty_protocols"] = any(
                    p.has_child_with(r'^\s*transport\s+input\s+ssh\b')
                    for p in vty_blocks
                )
            elif len(configuration["vty_protocols"]) > 1:
                results["vty_protocols"] = any(
                    p.has_child_with(r'^\s*transport\s+input\s+(?:all|telnet\s+ssh|ssh\s+telnet)\b')
                    for p in vty_blocks
                )

        return results

    def config(self, configuration: dict) -> list:
        """
        Generates configuration commands based on the provided configuration dictionary.

        Args:
            configuration (dict): The intended configuration values.

        Returns:
            list: A list of CLI command strings to be sent to the device.
        """
        nr = InitNornir(config_file="config/config.yaml")
        target = nr.filter(name=self.device_name)

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
        if "vty_protocols" in configuration:
            if len(configuration.get("vty_protocols")) > 1:
                config_lines.extend([
                    "line vty 0 15",
                    "transport input telnet ssh"
                ])
            elif len(configuration.get("vty_protocols")) == 1:
                config_lines.extend([
                    "line vty 0 15",
                    "transport input ssh"
                ])


        if "enable_passwd" in configuration:
            config_lines.append(f"enable secret {configuration['enable_passwd']}")

        return config_lines

    def save_config(self) -> bool:
        """
        Saves the current running configuration to startup configuration on the device.

        Returns:
            bool: True if successful, False otherwise.
        """
        nr = InitNornir(config_file="config/config.yaml")
        target = nr.filter(name=self.device_name)

        res = target.run(task=netmiko_save_config)
        host = list(target.inventory.hosts.keys())[0]
        if res[host].failed:
            return False
        else:
            return True

