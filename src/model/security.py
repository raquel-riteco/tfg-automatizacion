from typing import List


class Security:
    """
    Represents the security configuration of a network device, including password encryption,
    console access, VTY protocols, and enable password settings.
    """

    def __init__(self, is_encrypted: bool = False, console_access: str = None, enable_by_password: bool = False,
                 vty_protocols: List[str] = None):
        """
        Initializes the security settings for the device.

        Args:
            is_encrypted (bool): Whether passwords are encrypted.
            console_access (str): Type of console access method.
            enable_by_password (bool): Whether the enable mode requires a password.
            vty_protocols (List[str]): List of allowed VTY access protocols (e.g., ['ssh']).
        """
        self.is_encrypted = is_encrypted
        self.console_access = console_access
        self.enable_by_password = enable_by_password
        self.vty_protocols = vty_protocols

    def update(self, config_info: dict) -> None:
        """
        Updates the security settings based on the provided configuration dictionary.

        Args:
            config_info (dict): Dictionary containing optional keys to update security configuration.
        """
        if 'password_encryption' in config_info:
            self.is_encrypted = config_info['password_encryption']
        if 'console_access' in config_info:
            self.console_access = config_info['console_access']
        if 'vty_protocols' in config_info:
            self.vty_protocols = config_info['vty_protocols']
        if 'enable_passwd' in config_info:
            self.enable_by_password = config_info['enable_passwd']

    def get_info(self) -> dict:
        """
        Returns the full current security configuration as a dictionary.

        Returns:
            dict: Dictionary with keys for encryption, console access, enable password, and VTY protocols.
        """
        # When config is empty
        # console_access = None
        # enable_by_password = False
        # is_encrypted = False
        # vty_protocols = ['ssh']

        info = dict()
        info['is_encrypted'] = self.is_encrypted
        info['console_access'] = self.console_access
        info['enable_by_password'] = self.enable_by_password
        info['vty_protocols'] = self.vty_protocols
        return info

    def get_config(self) -> dict | None:
        """
        Returns a minimal configuration dictionary, excluding defaults.

        Returns:
            dict | None: Configuration dictionary or None if no non-default values are present.
        """
        info = dict()
        if self.console_access is not None:
            info['console_access'] = self.console_access
        if self.enable_by_password is True:
            info['enable_by_password'] = self.enable_by_password
        if self.is_encrypted is True:
            info['is_encrypted'] = self.is_encrypted
        if len(self.vty_protocols) > 1:
            info['vty_protocols'] = self.vty_protocols

        if len(info) > 0:
            return info

        return None

