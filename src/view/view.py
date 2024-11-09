from view_parser import ViewParser
from router_menu import RouterMenu


EXIT = -1


class View:
    def __init__(self):
        self.view_parser = ViewParser()
        self.router_menu = RouterMenu()
        
    
    # Returns 0 if no load config, 1 if load config    
    def start_menu(self, info: dict) -> int:
        return 0
    
    
    def main_menu(self) -> int:
        return 0
    
    
    def goodbye(self) -> None:
        print("\nGOODBYE!\n")