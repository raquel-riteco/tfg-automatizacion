

class Interface:
    def __init__(self, name: str, is_up: bool, description: str = None):
        self.name = name
        self.description = description
        self.is_up = is_up
        
        
    def update(self, config_info: dict) -> None:
        if config_info['iface_desc']: self.description = config_info['iface_desc']
        if config_info['iface_shutdown']: self.is_up = config_info['iface_shutdown']

    def get_info(self) -> dict:
        info = dict()
        info['description'] = self.description
        info['is_up'] = self.is_up
        return info