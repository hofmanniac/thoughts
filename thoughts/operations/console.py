from thoughts.operations.core import Operation
import thoughts.interfaces.messaging
from thoughts.context import Context

class ConsoleReader(Operation):
    monikers = ["ConsoleReader", "Ask"]
    def __init__(self, prompt, append_interaction_history = True):
        self.prompt = prompt
        self.condition = None
        self.append_interaction_history = append_interaction_history

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
        
        if self.append_interaction_history:
            context.push_message(human_message)

        return human_message, None

    @classmethod
    def parse_json(cls, json_snippet, config):
        moniker = "read" if "read" in json_snippet else "Ask" if "Ask" in json_snippet else "MessageReader"
        prompt = json_snippet[moniker]
        append_interaction_history = json_snippet.get("append_history", True)
        return cls(prompt=prompt, append_interaction_history = append_interaction_history)

class ConsoleWriter(Operation):
    def __init__(self, text = None, typing_speed=0.03, from_item = None):
        self.text = text
        self.typing_speed = typing_speed
        self.condition = None
        self.from_item = from_item

    def execute(self, context: Context, message = None, from_item = None):

        if self.text is not None:
            last_message = thoughts.interfaces.messaging.AIMessage(content=self.text)
        else:
            if self.from_item is not None:
                last_message = context.get_item(self.from_item)
                if type(last_message) is str:
                    last_message = thoughts.interfaces.messaging.AIMessage(content=last_message)
            elif message is not None:
                last_message = message
            else:
                last_message = context.get_last_message()

        last_message.print_content(self.typing_speed)

        return None, None
    
    @classmethod
    def parse_json(cls, json_snippet, config):
        # moniker = "Ask" if "Ask" in json_snippet else "MessageWriter"
        from_item = json_snippet.get("from", None)
        typing_speed = json_snippet.get("speed", 0.03)
        return cls(from_item=from_item, typing_speed=typing_speed)