import re

ALIAS_MAP = {
    "g": "GigabitEthernet",
    "gi": "GigabitEthernet",
    "gigabitethernet": "GigabitEthernet",
    "f": "FastEthernet",
    "fa": "FastEthernet",
    "fastethernet": "FastEthernet",
    "e": "Ethernet",
    "eth": "Ethernet",
    "ethernet": "Ethernet",
}

# Add optional subinterface: ".<digits>"
_iface_re = re.compile(
    r'^(?P<prefix>gigabitethernet|gi|g|fastethernet|fa|f|ethernet|eth|e)\s*'
    r'(?P<id>\d+(?:/\d+)*)'          # physical id: 0, 0/0, 0/0/1, ...
    r'(?:\.(?P<sub>\d+))?$'          # optional subinterface: .100
    , flags=re.IGNORECASE
)

def normalize_iface(name: str) -> str:
    s = name.strip().lower().replace(" ", "")
    m = _iface_re.fullmatch(s)
    if not m:
        # Not one of the Ethernet families normalize—return as-is for other types
        return s
    prefix = ALIAS_MAP[m.group("prefix")]
    base_id = m.group("id")
    sub = m.group("sub")
    return f"{prefix}{base_id}" + (f".{sub}" if sub else "")


class Interface:
    def __init__(self, name: str, is_up: bool, description: str = None):
        self.name = normalize_iface(name)
        self.description = description
        self.is_up = is_up
        
        
    def update(self, config_info: dict) -> None:
        if 'iface_desc' in config_info:
            self.description = config_info['iface_desc']
        if 'iface_shutdown' in config_info:
            self.is_up = not config_info['iface_shutdown']

    def get_info(self) -> dict:
        info = dict()
        info["name"] = self.name
        info['description'] = self.description
        info['is_up'] = self.is_up
        return info