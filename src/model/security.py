from typing import List

class Security:
    def __init__(self, is_encrypted: bool = False, console_by_passwd: bool = None, vty_by_passwd: bool = None, protocols: List[str] = None):
        self.is_encrypted = is_encrypted
        self.console_by_passwd = console_by_passwd
        self.vty_by_passwd = vty_by_passwd
        self.protocols = protocols
        
    def update(self, is_encrypted: bool = False, console_by_passwd: bool = None, vty_by_passwd: bool = None, protocols: List[str] = None) -> None:
        """
        Updates security settings for the device, including encryption, console and VTY access control,
        and enabled protocols.

        Args:
            is_encrypted (bool, optional): Indicates if security encryption is enabled. Defaults to False.
            console_by_passwd (bool, optional): Specifies if console access is secured by a password.
            vty_by_passwd (bool, optional): Specifies if VTY (Virtual Teletype) access is secured by a password.
            protocols (List[str], optional): List of security protocols enabled on the device (e.g., SSH, Telnet).

        Returns:
            None
        """
        self.is_encrypted = is_encrypted
        self.console_by_passwd = console_by_passwd
        self.vty_by_passwd = vty_by_passwd
        self.protocols = protocols