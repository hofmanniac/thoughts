from abc import abstractmethod

from thoughts.context import Context

class Operation():

    def __init__(self, name: str = None, description: str = None):
        self.name = name
        self.description = description
        self.condition = True

    @abstractmethod
    def should_execute(self, context: Context, message = None):
        return self.condition

    @abstractmethod
    def execute(self, context: Context, message = None):
        pass