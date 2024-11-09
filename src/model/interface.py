

class Interface:
    def __init__(self, name: str, is_up: bool, description: str = None):
        self.name = name
        self.description = description
        self.is_up = is_up
        
        
    def update(self, name: str, is_up: bool, description: str = None) -> None:
        self.name = name
        self.description = description
        self.is_up = is_up