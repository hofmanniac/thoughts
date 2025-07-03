import threading
from thoughts.operations.core import Operation
import thoughts.interfaces.messaging
from thoughts.context import Context
from thoughts.interfaces.speech import speak

class ConsoleReader(Operation):
    monikers = ["ConsoleReader", "Ask"]
    def __init__(self, prompt, append_interaction_history = True, save_into: str = None):
        self.prompt = prompt
        self.condition = None
        self.append_interaction_history = append_interaction_history
        self.save_into = save_into

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

        if self.save_into is not None:
            context.set_item(self.save_into, human_message.content)

        return human_message, None

    @classmethod
    def parse_json(cls, json_snippet, config):
        moniker = "read" if "read" in json_snippet else "Ask" if "Ask" in json_snippet else "MessageReader"
        prompt = json_snippet[moniker]
        append_interaction_history = json_snippet.get("append_history", True)
        save_into = json_snippet.get("into", None)
        return cls(prompt=prompt, append_interaction_history = append_interaction_history, save_into=save_into)

class ConsoleWriter(Operation):
    def __init__(self, text = None, typing_speed=0.02, from_item = None, message_provider: Operation = None):
        self.message_provider: Operation = message_provider
        self.text = text
        self.typing_speed = typing_speed
        self.condition = None
        self.from_item = from_item
        self.console_done = threading.Event()
        self.speak_done = threading.Event()
    
    def run_console_type(self, line, typing_speed):
        thoughts.interfaces.messaging.console_type(text=line, typing_speed=typing_speed)
        self.console_done.set()  # Signal that console typing is done

    def run_speak(self, line):
        speak(line, voice="af_nicole")
        self.speak_done.set()  # Signal that speaking is done

    def execute(self, context: Context, message = None):

        if self.text is not None:
            last_message = thoughts.interfaces.messaging.AIMessage(content=self.text)
        else:
            if self.from_item is not None:
                last_message = context.get_item(self.from_item)
                if type(last_message) is str:
                    last_message = thoughts.interfaces.messaging.AIMessage(content=last_message)
            elif self.message_provider is not None:
                last_messages, _ = self.message_provider.execute(context, message)
                last_message = last_messages[0]
            elif message is not None:
                last_message = message
            else:
                last_message = context.get_last_message()

        if type(last_message) is str:
            last_message = thoughts.interfaces.messaging.AIMessage(content=last_message)
        
        if type(last_message) is list:
            for msg in last_message:
                print(msg)
        else:
            text = last_message.content
            lines = text.split("\n")
            
            # Clear events at the beginning of each iteration
            self.console_done.clear()
            self.speak_done.clear()

            for line in lines:
                # print(f'{last_message.speaker}:', end=" ")
                # thoughts.interfaces.messaging.console_type(text=line, typing_speed=self.typing_speed)
                # speak(line, voice="af_nicole")
                # Create threads for console typing and speaking
                console_thread = threading.Thread(target=self.run_console_type, args=(line, self.typing_speed))
                speak_thread = threading.Thread(target=self.run_speak, args=(line,))

                # Start both threads
                console_thread.start()
                speak_thread.start()

                # Optionally, wait for both threads to finish if needed (remove these if you want them to run asynchronously)
                # self.console_done.wait()
                # self.speak_done.wait()

                console_thread.join()
                speak_thread.join()

        return None, None
    
    @classmethod
    def parse_json(cls, json_snippet, config):
        # moniker = "Ask" if "Ask" in json_snippet else "MessageWriter"
        
        # message_provider = "#" # default to last message
        message_provider = None
        moniker_value = json_snippet.get("Write", None)
        text = None
        if type(moniker_value) is str and moniker_value != "#":
            text = moniker_value 
        elif type(moniker_value) is dict:
            from thoughts.parser import ConfigParser
            message_provider = ConfigParser.parse_operation(moniker_value, config)

        # message_provider_config = moniker_value if type(moniker_value) is dict else None
        # if message_provider_config is not None:
        #     from thoughts.parser import ConfigParser
        #     message_provider = ConfigParser.parse_operation(config, message_provider_config)
        # else:

        from_item = json_snippet.get("from", None)
        typing_speed = json_snippet.get("speed", 0.02)
        # text = json_snippet.get("text", None)

        return cls(from_item=from_item, typing_speed=typing_speed, 
                   message_provider=message_provider, text=text)