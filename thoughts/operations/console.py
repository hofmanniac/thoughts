from thoughts.operations.core import Operation
import thoughts.interfaces.messaging
from thoughts.engine import Context
from thoughts.interfaces.messaging import AIMessage

class ConsoleReader(Operation):
    def __init__(self, prompt):
        self.prompt = prompt
        self.condition = None

    def _debug_loop(self, context: Context):
        while True:
            command = input("> ")
            if command == "memory":
                parm = input("Key?")
                items = context.get_item(parm, None)
                if items is None:
                    print("Key not found")
                    continue
                if type(items) is list:
                    for item in items:
                        print(item)
                else:
                    print(items)
            elif command == "exit":
                break

    def execute(self, context: Context, message = None):
        human_message = thoughts.interfaces.messaging.console_input(console_prompt=self.prompt)

        if human_message.content == "debug":
            self._debug_loop(context)
            return None, False
        elif human_message.content == "exit":
            return None, True # exit app
        else:    
            context.push_message(human_message)

        return human_message, None

class ConsoleWriter(Operation):
    def __init__(self, text = None, typing_speed=0.03):
        self.text = text
        self.typing_speed = typing_speed
        self.condition = None

    def execute(self, context: Context, message = None):

        if self.text is None:
            if message is not None:
                last_message = message
            else:
                last_message = context.get_last_message()
        else:
            last_message = thoughts.interfaces.messaging.AIMessage(content=self.text)

        last_message.print_content(self.typing_speed)

        return None, None