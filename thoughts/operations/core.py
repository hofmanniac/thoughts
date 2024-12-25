from abc import abstractmethod

class Operation():

    def __init__(self, description: str = ""):
        self.description = description
    
    @abstractmethod
    def execute(self, *args, **kwargs):
        pass

