from loguru import logger

class ClientState:
    """
    Singleton of Clients State. 
    
    Stores meaningful data used to run or modify the program.
    """
    _instance = None

    def __init__(self):
        self.
        pass

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance


