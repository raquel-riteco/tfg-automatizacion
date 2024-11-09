from view.view_parser import ViewParser
from view.router_menu import RouterMenu

from os import listdir
from dataclasses import dataclass

MAIN_MENU = ["MAIN MENU", "Add device", "Remove device", "Show network", "Modify config", "Subnetting", "Exit"]


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
        
        
    def __show_menu__(self, menu: list) -> int:
        """
        Displays a menu from a given list and returns the selected option as an integer.
        If the user selects the last option, the function returns EXIT.
        
        Args:
            menu (list): List containing menu options where the first element is the menu title.

        Returns:
            int: The selected menu option or EXIT if the last option is chosen.
        """
        
        option = 0
        options = Option()
        
        while(True):
            print(f"{menu[0]}\n")
            for i in range(1, len(menu)):
                print(f"\t{i}. {menu[i]}")
            option = input(f"\nEnter option: ")
            try:
                option = int(option)
                if (option < 1 or option > len(menu) - 1):
                    print(self.parser.parse_error("Invalid option."))
                elif (option == len(menu) - 1):
                    return options.exit
                else:
                    return option
            except ValueError:
                option = 0
                print(self.parser.parse_error("Invalid option."))
                
                
                
    # Returns 0 if no load config, 1 if load config    
    def start_menu(self, info: dict) -> int:
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
        # Get main menu option
        option = self.__show_menu__(MAIN_MENU)
        
        return option
    
    
    def goodbye(self) -> None:
        print("\nGOODBYE!\n")
        
        
        
if __name__=="__main__":
    view = View()
    info = dict()
    
    option = view.start_menu(info)