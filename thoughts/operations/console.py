from thoughts.operations.core import Operation
import thoughts.interfaces.messaging
from thoughts.engine import Context

class ConsoleReader(Operation):
    def __init__(self, prompt):
        self.prompt = prompt

    def execute(self, context: Context):
        human_message = thoughts.interfaces.messaging.console_input(console_prompt=self.prompt)
        context.push(human_message)

class ConsoleWriter(Operation):
    def __init__(self, typing_speed=0.03):
        self.typing_speed = typing_speed

    def execute(self, context: Context):
        message = context.get_last_message()
        thoughts.interfaces.messaging.console_type(message=message, typing_speed=self.typing_speed)