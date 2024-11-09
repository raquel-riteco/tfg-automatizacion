from view_parser import ViewParser
from router_menu import RouterMenu

from dataclasses import dataclass


@dataclass
class Option:
    # Main menu options
    exit:           int = -1
    add_device:     int = 1
    remove_device:  int = 2
    show_network:   int = 3
    modify_config:  int = 4
    subnetting:     int = 5


class View:
    def __init__(self):
        self.view_parser = ViewParser()
        self.router_menu = RouterMenu()
        
    
    # Returns 0 if no load config, 1 if load config    
    def start_menu(self, info: dict) -> int:
        return 0
    
    
    def main_menu(self, info: dict) -> int:
        return 0
    
    
    def goodbye(self) -> None:
        print("\nGOODBYE!\n")