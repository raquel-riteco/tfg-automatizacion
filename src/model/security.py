from typing import List

class Security:
    def __init__(self, is_encrypted: bool = False, console_by_password: bool = False, enable_by_password: bool = False,
                 protocols: List[str] = None):
        self.is_encrypted = is_encrypted
        self.console_by_password = console_by_password
        self.enable_by_password = enable_by_password
        self.protocols = protocols
        
    def update(self, is_encrypted: bool = False, console_by_password: bool = False, enable_by_password: bool = False,
                 protocols: List[str] = None) -> None:
        """
        Updates security settings for the device, including encryption, console and VTY access control,
        and enabled protocols.

        Args:
            is_encrypted (bool, optional): Indicates if security encryption is enabled. Defaults to False.
            console_by_password (bool, optional): Specifies if console access is secured by a password.
            enable_by_password (bool, optional): Specifies if enable access is secured by a password.
            protocols (List[str], optional): List of security protocols enabled on the device (e.g., SSH, Telnet).

        Returns:
            None
        """
        if is_encrypted: self.is_encrypted = is_encrypted
        if console_by_password: self.console_by_password = console_by_password
        if enable_by_password: self.enable_by_password = enable_by_password
        if protocols: self.protocols = protocols

    def get_info(self) -> dict:
        info = dict()
        info['is_encrypted'] = self.is_encrypted
        info['console_by_password'] = self.console_by_password
        info['enable_by_password'] = self.enable_by_password
        info['protocols'] = self.protocols
        return info
