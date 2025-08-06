
from typing import List, cast
from ipaddress import IPv4Address
from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get, napalm_configure
from ciscoconfparse import CiscoConfParse

from model.security import Security

class Device:
    def __init__(self, hostname: str, mgmt_ip: IPv4Address, mgmt_iface: str, security: dict = None,
                 users: List[dict] = None, banner: str = None):
        self.security = Security(security["is_encrypted"], security["console_by_password"],
                                 security['enable_by_password'], security["protocols"])
        self.hostname = hostname
        self.mgmt_ip = mgmt_ip
        self.mgmt_iface = mgmt_iface
        self.users = users
        self.banner = banner
        

    def update(self, hostname: str, security: dict, users: List[dict], banner: str = None) -> None:
        """
        Updates device settings, including hostname, interfaces, security configurations, users, and banner.

        Sets the hostname, updates each interface with specified attributes, adjusts security settings, 
        and updates the list of users and optional device banner.

        Args:
            hostname (str): The hostname of the device.
            security (dict): Dictionary containing security settings, including:
                - is_encrypted (bool): Indicates if security encryption is enabled. Defaults to False.
                - console_by_password (bool): Specifies if console access is secured by a password.
                - enable_by_password (bool): Specifies if enable access is secured by a password.
                - vty_by_password (bool): Specifies if VTY (Virtual Teletype) access is secured by a password.
                - vty_login_local (bool): Specifies if VTY (Virtual Teletype) access is done by local users.
                - protocols (List[str]): List of security protocols enabled on the device (e.g., SSH, Telnet).
            users (List[dict]): List of dictionaries with user information.
            banner (str, optional): Device banner message.

        Returns:
            None
        """
        if hostname: self.hostname = hostname
        if security: self.security.update(security.get("is_encrypted"), security.get("console_by_password"),
                                          security.get('enable_by_password'), security.get("protocols"))
        if users: self.users = users
        if banner: self.banner = banner
        
        
    def get_device_info(self) -> dict:
        device_info = dict()
        device_info["device_name"] = self.hostname
        device_info["mgmt_iface"] = self.mgmt_ip
        device_info["mgmt_ip"] = self.mgmt_iface
        return device_info


    def config(self, configuration: dict) -> None:
        """
            Applies configuration to the device using NAPALM (via Nornir).

            Args:
                configuration (dict): Configuration instructions.

            Raises:
                RuntimeError: If configuration fails.
        """
        nr = InitNornir(config_file="config/config.yaml")
        target = nr.filter(name=self.hostname)

        config_lines = []

        # BASIC CONFIG
        if "hostname" in configuration:
            config_lines.append(f"hostname {configuration['hostname']}")

        if "domain_lookup" in configuration:
            if configuration["domain_lookup"]:
                config_lines.append("ip domain-lookup")
            else:
                config_lines.append("no ip domain-lookup")

        for user in configuration.get("users_to_add", []):
            config_lines.append(
                f"username {user['username']} privilege {user.get('privilege', 1)} secret {user['password']}")

        for user in configuration.get("users_to_remove", []):
            config_lines.append(f"no username {user}")

        if "banner" in configuration:
            banner = configuration["banner"].replace("^", "")
            config_lines.append(f"banner motd ^{banner}^")

        # SECURITY CONFIG
        if configuration.get("encrypt_passwords"):
            config_lines.append("service password-encryption")

        if configuration.get("console_access"):
            config_lines.extend([
                "line console 0",
                "login local"
            ])

        if configuration.get("vty_access"):
            config_lines.extend([
                "line vty 0 4",
                "login local"
            ])

        if "enable_secret" in configuration:
            config_lines.append(f"enable secret {configuration['enable_secret']}")

        if not config_lines:
            print("No configuration to apply.")
            return

        # Send configuration to the device
        result = target.run(
            task=napalm_configure,
            configuration="\n".join(config_lines),
        )

        task_result = result[self.hostname]

        if task_result.failed:
            raise RuntimeError(f"NAPALM configuration failed: {task_result.exception}")

        print(f"Configuration applied successfully to {self.hostname}.")
        print("Applied commands:")
        for line in config_lines:
            print(f"  {line}")

