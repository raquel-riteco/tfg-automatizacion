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
    """
    Normalizes interface names to Cisco's full format.

    Args:
        name (str): Interface name, possibly abbreviated (e.g., "g0/1", "fa 0/0").

    Returns:
        str: Normalized interface name (e.g., "GigabitEthernet0/1").
    """
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
    """
    Represents a Layer 3 interface on a network device.

    Attributes:
        name (str): The interface name, normalized.
        is_up (bool): Interface operational status.
        description (str, optional): Description of the interface.
    """

    def __init__(self, name: str, is_up: bool, description: str = None):
        """
        Initializes an Interface instance.

        Args:
            name (str): Interface name (e.g., "g0/1").
            is_up (bool): Operational state of the interface.
            description (str, optional): Optional interface description.
        """
        self.name = normalize_iface(name)
        self.description = description
        self.is_up = is_up

    def update(self, config_info: dict) -> None:
        """
        Updates interface properties based on the provided config.

        Args:
            config_info (dict): Configuration dictionary. May include:
                - 'description' (str)
                - 'is_up' (bool)
        """
        if 'description' in config_info:
            self.description = config_info['description']
        if 'is_up' in config_info:
            self.is_up = config_info['is_up']

    def get_info(self) -> dict:
        """
        Returns a complete snapshot of interface state.

        Returns:
            dict: Dictionary containing:
                - 'name' (str)
                - 'description' (str or None)
                - 'is_up' (bool)
        """
        # When config is empty:
        # name is the normalized name of the interface
        # is_up is True or False
        # description is None
        info = dict()
        info["name"] = self.name
        info['description'] = self.description
        info['is_up'] = self.is_up
        return info

    def get_config(self) -> dict:
        """
        Returns the interface configuration.

        Returns:
            dict: Configuration dictionary including:
                - 'name' (str)
                - 'description' (if not None)
                - 'is_up' (bool)
        """
        info = dict()
        info["name"] = self.name
        if self.description is not None:
            info['description'] = self.description
        info['is_up'] = self.is_up
        return info

