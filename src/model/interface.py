

class Interface:
    def __init__(self, name: str, is_up: bool, description: str = None):
        self.name = name
        self.description = description
        self.is_up = is_up
        
        
    def update(self, config_info: dict) -> None:
        if 'iface_desc' in config_info: self.description = config_info['iface_desc']
        if 'iface_shutdown' in config_info: self.is_up = config_info['iface_shutdown']

    def get_info(self) -> dict:
        info = dict()
        info["name"] = self.name
        info['description'] = self.description
        info['is_up'] = self.is_up
        return info