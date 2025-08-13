from typing import List

class Security:
    def __init__(self, is_encrypted: bool = False, console_access: str = None, enable_by_password: bool = False,
                 vty_protocols: List[str] = None):
        self.is_encrypted = is_encrypted
        self.console_access = console_access
        self.enable_by_password = enable_by_password
        self.vty_protocols = vty_protocols
        
    def update(self, config_info: dict) -> None:

        if 'password_encryption'in config_info: self.is_encrypted = config_info['password_encryption']
        if 'console_access' in config_info: self.console_access = config_info['console_access']
        if 'vty_protocols' in config_info: self.vty_protocols = config_info['vty_protocols']
        if 'enable_passwd' in config_info: self.enable_by_password = config_info['enable_passwd']

    def get_info(self) -> dict:
        info = dict()
        info['is_encrypted'] = self.is_encrypted
        info['console_access'] = self.console_access
        info['enable_by_password'] = self.enable_by_password
        info['vty_protocols'] = self.vty_protocols
        return info
