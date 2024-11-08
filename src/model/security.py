from typing import List

class Security:
    def __init__(self, is_encrypted: bool = False, console_by_passwd: bool = None, vty_by_passwd: bool = None, protocols: List[str] = None):
        self.is_encrypted = is_encrypted
        self.console_by_passwd = console_by_passwd
        self.vty_by_passwd = vty_by_passwd
        self.protocols = protocols
        
    def update(self, is_encrypted: bool = False, console_by_passwd: bool = None, vty_by_passwd: bool = None, protocols: List[str] = None) -> None:
        self.is_encrypted = is_encrypted
        self.console_by_passwd = console_by_passwd
        self.vty_by_passwd = vty_by_passwd
        self.protocols = protocols