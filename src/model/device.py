
from typing import List

from security import Security
from interface import Interface

class Device:
    def __init__(self):
       self.security = Security()
       self.interfaces = List[Interface] 
       