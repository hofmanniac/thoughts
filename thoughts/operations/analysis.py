from thoughts.engine import Context
from thoughts.operations.core import Operation
from thoughts.operations.prompting import PromptRunner

class Analyzer(Operation):
    
    def __init__(self, prompt_name, value_provider, value_keeper):
        self.prompt_name = prompt_name
        self.value_provider = value_provider
        self.value_keeper = value_keeper

    def _analyze(self, context: Context, items):
        runner = PromptRunner(self.prompt_name)
        results, control = runner.execute(context)
        return results
        
    def execute(self, context: Context, message = None):
        items = self.value_provider.execute(context)
        conclusions = self._analyze(items)
        self.value_keeper.execute(context, conclusions)
        return conclusions, None
        