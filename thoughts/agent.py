import json
from thoughts.context import Context
from thoughts.operations.core import Operation
from thoughts.operations.routing import Choice
from thoughts.operations.workflow import PipelineExecutor

class Agent(Operation):
    def __init__(self):
        self.behaviors = []

    def load_from_config(self, context: Context, config_path):
        
        with open(config_path, 'r') as file:
            config = json.load(file)

        self.name = config.get("name", "Unnamed Agent")
        
        behaviors = config.get("Behaviors", [])
        for behavior in behaviors:
            if "Task" in behavior:
                task = PipelineExecutor.parse_json(behavior, config)
                self.behaviors.append(task)
            elif "Choice" in behavior:
                choice = Choice.parse_json(behavior, config)
                self.behaviors.append(choice)

        items = config.get("Items", [])
        # Set each item in the context using the first property as the item name and value
        for item in items:
            if isinstance(item, dict):
                for key, value in item.items():
                    context.set_item(key, value)
                    break  # Only use the first property

    def execute(self, context: Context, message = None):
        behavior_name = message
        behavior: Operation

        if message is not None:
            for behavior in self.behaviors:
                if behavior.name == behavior_name:
                    behavior.execute(context, None) # message is used only to select the behavior
        else:
            behavior = self.behaviors[0]
            behavior.execute(context, None)