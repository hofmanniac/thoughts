from abc import abstractmethod

from thoughts.context import Context

class Operation():
    monikers = []
    def __init__(self, name: str = None, description: str = None):
        self.name = name
        self.description = description
        self.condition = True

    def get_first_moniker(json_snippet, monikers):
        return next((moniker for moniker in monikers if moniker in json_snippet), None)  

    @abstractmethod
    def should_execute(self, context: Context, message = None):
        return self.condition

    @abstractmethod
    def execute(self, context: Context, message = None):
        pass