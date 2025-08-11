

class Interface:
    def __init__(self, name: str, is_up: bool, description: str = None):
        self.name = name
        self.description = description
        self.is_up = is_up
        
        
    def update(self, is_up: bool, description: str = None) -> None:
        """
        Updates the interface attributes, including name, status, and optional description.

        Sets the name, operational status, and description for the interface.

        Args:
            is_up (bool): The operational status of the interface (True if up, False if down).
            description (str, optional): A description for the interface.

        Returns:
            None
        """
        if description: self.description = description
        if is_up: self.is_up = is_up

    def get_info(self) -> dict:
        info = dict()
        info['description'] = self.description
        info['is_up'] = self.is_up
        return info