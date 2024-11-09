from view_parser import ViewParser
from router_menu import RouterMenu

from os import listdir
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
        self.parser = ViewParser()
        self.router_menu = RouterMenu()
        
    
    # Returns 0 if no load config, 1 if load config    
    def start_menu(self, info: dict) -> int:
        info = dict()
        info["defaults"] = dict()
        path = "db/"
        string = ""
        
        # Get information for defaults file in inventory
        while not string:
            string = input("Enter username: ")
        info["defaults"]["username"] = string
        
        string = ""
        while not string:
            string = input("Enter password: ")
        info["defaults"]["password"] = string
        
        while True:
            option = input("Do you want to load a hosts file (Y | N)? ")
            if option:
                match option.lower():
                    case 'y':
                        while True:
                            # Show current files in db/
                            files = listdir(path)
                            print("Configuration files:")
                            for file in files:
                                print(f"\t- {file}")
                            # Get filename
                            string = input("Enter hosts filename: ")
                            try:
                                open(path + string, "r")
                                info["filename"] = path + string
                                return 1
                            except IOError:
                                # Filename not found
                                print(self.parser.parse_error(f"Could not find file {string} in {path}."))
                            
                    case 'n':
                        return 0       
                
    
    
    def main_menu(self, info: dict) -> int:
        return 0
    
    
    def goodbye(self) -> None:
        print("\nGOODBYE!\n")
        
        
        
if __name__=="__main__":
    view = View()
    info = dict()
    
    option = view.start_menu(info)