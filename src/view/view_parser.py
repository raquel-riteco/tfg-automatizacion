ESC             = "\x1b"
RESET_ALL       = f"{ESC}[0m"
ERROR           = f"{ESC}[38;5;196m"  # Red
WARNING         = f"{ESC}[38;5;208m"  # Orange
NOT_AVAILABLE   = f"{ESC}[38;5;245m"  # Grey
OK              = f"{ESC}[92m"        # Green
DEBUG           = f"{ESC}[38;5;39m"  # Blue


class ViewParser:
    def __init__(self):
        pass
  
    def parse_error(self, msg: str) -> str:
        return f"{ERROR}ERROR: {msg}{RESET_ALL}"
            
    def parse_warning(self, msg: str) -> str:
        return f"{WARNING}WARNING: {msg}{RESET_ALL}"

    def parse_not_available(self, msg: str) -> str:
        return f"{NOT_AVAILABLE}{msg}{RESET_ALL}"

    def parse_ok(self, msg: str) -> str:
        return f"{OK}{msg}{RESET_ALL}"
      
    def parse_debug(self, msg: str) -> str:
        return f"{DEBUG}DEBUG: {msg}{RESET_ALL}"
    
    
    
if __name__ == "__main__":
    parser = ViewParser()
    print(parser.parse_error("This is an error"))
    print(parser.parse_not_available("This is not available"))
    print(parser.parse_warning("This is a warning"))
    print(parser.parse_ok("This is ok"))
    print(parser.parse_debug("This is debug"))