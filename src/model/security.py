from typing import List

class Security:
    def __init__(self, is_encrypted: bool = False, console_by_password: str = None, enable_by_password: bool = False,
                 protocols: List[str] = None):
        self.is_encrypted = is_encrypted
        self.console_by_password = console_by_password
        self.enable_by_password = enable_by_password
        self.protocols = protocols
        
    def update(self, config_info: dict) -> None:

        if config_info['password_encryption']: self.is_encrypted = config_info['password_encryption']
        if config_info['console_access']: self.console_by_password = config_info['console_access']
        if config_info['vty_protocols']: self.protocols = config_info['vty_protocols']
        if config_info['enable_passwd']: self.enable_by_password = config_info['enable_passwd']

    def get_info(self) -> dict:
        info = dict()
        info['is_encrypted'] = self.is_encrypted
        info['console_by_password'] = self.console_by_password
        info['enable_by_password'] = self.enable_by_password
        info['protocols'] = self.protocols
        return info
