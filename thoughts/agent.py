import json
from thoughts.context import Context
from thoughts.operations.core import Operation, OperationResult
from thoughts.operations.routing import Choice
from thoughts.operations.thought import Express
from thoughts.operations.workflow import PipelineExecutor
from thoughts.parser import ConfigParser

class Agent(Operation):
    
    def __init__(self):
        self.steps = []

    def load_from_config(context: Context, config_path):
        
        with open(config_path, 'r') as file:
            config = json.load(file)

        agent = Agent()
        agent.name = config.get("name", "")
        
        steps = config.get("Steps", [])
        for step_config in steps:
            step = ConfigParser.parse_operation(step_config, config)
            agent.steps.append(step)

        items = config.get("Items", [])
        # Set each item in the context using the first property as the item name and value
        for item in items:
            if isinstance(item, dict):
                for key, value in item.items():
                    context.set_item(key, value)
                    break  # Only use the first property

        return agent

    def execute(self, context: Context, message = None) -> OperationResult:
        results = []
        step: Operation
        for step in self.steps:
            if not step.should_execute(context, message):
                continue
            operation_result = step.execute(context, message)
            results.extend(operation_result.messages)
        return OperationResult(messages=results, control=None)