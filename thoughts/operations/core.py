from abc import abstractmethod
from thoughts.context import Context

class OperationResult():
    result = None
    control = True

class Operation():
    
    monikers = []
    condition = None
    context: Context = None

    def __init__(self, name: str = None, description: str = None, context: Context = None):
        self.context = context if context is not None else Context()
        self.name = name
        self.description = description
        self.condition = None

    def get_first_moniker(json_snippet, monikers):
        return next((moniker for moniker in monikers if moniker in json_snippet), None)  

    def resolve_context(self, context: Context):
        if context is None:
            return self.context
        return context
    
    @abstractmethod
    def should_execute(self, context: Context, message = None):
        return self.condition

    @abstractmethod
    def execute(self, context: Context, message = None):
        pass

    @abstractmethod
    def process(self, message = None, context: Context = None):
        pass