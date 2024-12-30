from thoughts.interfaces.messaging import AIMessage, HumanMessage, PromptMessage, SystemMessage
from thoughts.operations.console import ConsoleWriter
from thoughts.operations.core import Operation
import thoughts.interfaces.prompting
from thoughts.engine import Context
# from thoughts.operations.memory import ContextMemoryAppender, MemoryKeeper
from thoughts.util import convert_to_list

from enum import Enum, auto

class RunCondition(Enum):
    ALWAYS = auto()
    CONTINUATION = auto()
    START = auto()

def should_execute(context: Context, run_condition: RunCondition):
    if run_condition == RunCondition.ALWAYS:
        return True
    elif run_condition == RunCondition.CONTINUATION and context.messages:
        return True
    elif run_condition == RunCondition.START and not context.messages:
        return True
    return False

def format_content(content):
    if isinstance(content, list):
        return "\n".join(format_content(item) for item in content)
    elif isinstance(content, dict):
        return ", ".join(f"{k}: {format_content(v)}" for k, v in content.items())
    elif isinstance(content, str):
        return content
    else:
        return str(content)

def get_first_moniker(json_snippet, monikers):
    return next(moniker for moniker in monikers if moniker in json_snippet)  

def create_moniker_mapping(base_class):
    moniker_mapping = {}
    
    def add_subclasses(cls):
        for subclass in cls.__subclasses__():
            for moniker in getattr(subclass, 'monikers', []):
                moniker_mapping[moniker] = subclass
            add_subclasses(subclass)
    
    add_subclasses(base_class)
    return moniker_mapping

class DictFormatter(dict):
    def __missing__(self, key):
        return '{' + key + '}'
    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        if isinstance(value, list):
            return '\n'.join(str(item) for item in value)
        elif isinstance(value, dict):
            return ', '.join(f"{k}: {v}" for k, v in value.items())
        return value

class MessageStarter(Operation):
    def __init__(self, role: str, content: str = None, file: str = None):
        self.condition = None
        self.role = role
        self.file = file
        self.content = content
    def execute(self, context: Context, messages = None):
        
        if self.file is not None:
            base_path = context.content_path + "/" if context.content_path is not None else ""
            prompt = thoughts.interfaces.prompting.load_template(base_path + self.file)
            content = prompt["content"]
        else:
            content = self.content
        
        if messages is None:
            messages = []

        if self.role == "system":
            messages.append(SystemMessage(content=content))
        elif self.role == "ai":
            messages.append(AIMessage(content=content))
        elif self.role == "human":
            messages.append(HumanMessage(content=content))
        
        return messages, None
    
    @classmethod
    def parse_json(cls, json_snippet, config):
        if type(json_snippet) is str:
            return cls(role="human", content=json_snippet)
        elif type(json_snippet) is dict:
            moniker = "AIMessage" if "AIMessage" in json_snippet else "HumanMessage" if "HumanMessage" in json_snippet else "MessageStarter"
            if moniker == "AIMessage":
                role = "ai"
            elif moniker == "HumanMessage":    
                role = "human"
            elif moniker == "SystemMessage":
                role = "system" 
            else:
                role = json_snippet.get("role", "human")
            return cls(role=role, content=json_snippet[moniker])
    
class Role(Operation):
    """
    Start a new prompt.

    - If file is provided, loads the prompt from the template specified in prompt_name.
    - IF file is not provied, uses the content. 
    - If content is not provided, uses the default "You are a helpful AI assistant." prompt.

    Returns a single message in a list, for subsequent operations to append to.
    """
    monikers = ["Role"]
    def __init__(self, content: str = "You are a helpful AI assistant.", file: str = None):
        self.condition = None
        self.content = content
        self.file = file
    def execute(self, context: Context, messages = None, run_condition: RunCondition = RunCondition.ALWAYS):
        if not should_execute(context, run_condition):
            return messages, None
        message_starter = MessageStarter(role="system", content=self.content, file=self.file)
        return message_starter.execute(context, messages)
    @classmethod
    def parse_json(cls, json_snippet, config):
        if type(json_snippet) is str:
            return cls(content=json_snippet)
        elif type(json_snippet) is dict:
            moniker = get_first_moniker(json_snippet, cls.monikers)
            file = json_snippet.get("file", None)
            return cls(content=json_snippet[moniker], file=file)
        return None
    
class StartRole(Role):
    monikers = ["StartRole"]
    def execute(self, context: Context, messages=None):
        return super().execute(context, messages, RunCondition.START)
    
class ContinueRole(Role):
    monikers = ["ContinueRole"]
    def execute(self, context: Context, messages=None):
        return super().execute(context, messages, RunCondition.CONTINUATION)
    
class IncludeContext(Operation):
    monikers = ["Context", "IncludeContext"]
    def __init__(self, title: str = None, content: str = None, from_item: str = None, file: str = None ):
        self.condition = None
        self.title = title
        self.content = content
        self.from_item = from_item
        self.file = file
    def execute(self, context: Context, messages = None, run_condition: RunCondition = RunCondition.ALWAYS):

        if not messages or not should_execute(context, run_condition):         
            return messages, None
        
        prompt_message: PromptMessage = messages[-1] if messages else None
    
        content = None
        if self.content is not None:
            content = format_content(self.content)
        elif self.from_item is not None:
            content = context.get_item(self.from_item)
            content = format_content(content)
        elif self.file is not None:
            base_path = context.content_path + "/" if context.content_path is not None else ""
            prompt = thoughts.interfaces.prompting.load_template(base_path + self.file)
            content = prompt["content"]

        if self.title is not None and content is None:
            content = self.title
        elif self.title is not None:
            content = self.title + ":\n" + content
            
        prompt_message.content += "\n\n" + content
        return messages, None
    @classmethod
    def parse_json(cls, json_snippet, config):
        moniker = get_first_moniker(json_snippet, cls.monikers)
        title = json_snippet.get(moniker, None)
        content = json_snippet.get("content", None)
        from_item = json_snippet.get("key", None)
        file = json_snippet.get("file", None)
        if content is None and title is not None:
            content = title
            title = None
        return cls(title=title, content=content, from_item=from_item, file=file)

class StartContext(IncludeContext):
    monikers = ["Start", "StartContext"]
    def execute(self, context: Context, messages=None):
        return super().execute(context, messages, RunCondition.START)
        
class ContinueContext(IncludeContext):
    monikers = ["Continue", "ContinueContext"]
    def execute(self, context: Context, messages=None):
        return super().execute(context, messages, RunCondition.CONTINUATION)
    
class IncludeItem(IncludeContext):
    monikers = ["Item", "IncludeItem"]
    def __init__(self, title: str = None, key: str = None):
        if key is None:
            key = title
            title = None
        super().__init__(title=title, from_item=key)
    @classmethod
    def parse_json(cls, json_snippet, config):
        moniker = get_first_moniker(json_snippet, cls.monikers)
        title = json_snippet.get(moniker, None)
        key = json_snippet.get("key", None)
        return cls(title=title, key=key)
    
class ContinueItem(IncludeItem):
    monikers = ["ContinueItem"]
    def execute(self, context: Context, messages=None):
        return super().execute(context, messages, run_condition=RunCondition.CONTINUATION)
    
class StartItem(IncludeItem):
    monikers = ["StartItem"]
    def execute(self, context: Context, messages=None):
        return super().execute(context, messages, run_condition=RunCondition.START)
    
class IncludeFile(IncludeContext):
    monikers = ["File", "IncludeFile"]
    def __init__(self, title: str = None, file: str = None):
        if file is None:
            file = title
            title = None
        super().__init__(title=title, file=file)
    @classmethod
    def parse_json(cls, json_snippet, config):
        moniker = get_first_moniker(json_snippet, cls.monikers)
        title = json_snippet.get(moniker, None)
        file = json_snippet.get("file", None)
        return cls(title=title, file=file)
    
class ContinueFile(IncludeFile):
    monikers = ["ContinueFile"]
    def execute(self, context: Context, messages=None):
        return super().execute(context, messages, run_condition=RunCondition.CONTINUATION)
    
class StartFile(IncludeFile):
    monikers = ["StartFile"]
    def execute(self, context: Context, messages=None):
        return super().execute(context, messages, run_condition=RunCondition.START)

class IncludeHistory(Operation):
    """
    Loads a specified number of recent messages from the context's message history 
    and appends them to an existing list of messages.

    Behavior:
        - Retrieves a specified number of past messages from the context using `peek_messages`.
        - Adds the retrieved messages to the provided list, or initializes a new list if none is given.
        - Returns the updated list of messages.

    Args:
        context (Context): The context object used to retrieve message history.
        messages (list, optional): A list of messages to extend with the loaded message history. 
            If not provided, a new list is initialized.

    Returns:
        tuple:
            - The updated list of messages including the loaded message history.
            - None (placeholder for additional return data, unused in this implementation).
    """
    monikers = ["History", "IncludeHistory"]
    def __init__(self, num_messages: int = 4):
        self.condition = None
        self.num_messages = num_messages
    def execute(self, context: Context, messages = None, run_condition: RunCondition = RunCondition.ALWAYS):
        message_history = context.peek_messages(self.num_messages)
        if messages is None:
            messages = []
        messages.extend(message_history)
        return messages, None
    @classmethod
    def parse_json(cls, json_snippet, config):
        moniker = get_first_moniker(json_snippet, cls.monikers)
        return cls(num_messages=json_snippet[moniker])
    
class StartHistory(IncludeHistory):
    momikers = ["StartHistory"]
    def execute(self, context: Context, messages=None):
        return super().execute(context, messages, run_condition=RunCondition.START)
    
class ContinueHistory(IncludeHistory):
    monikers = ["ContinueHistory"]
    def execute(self, context: Context, messages=None):
        return super().execute(context, messages, run_condition=RunCondition.CONTINUATION)
    
class Instruction(Operation):
    monikers = ["Instruction", "IncludeInstruction"]
    def __init__(self, content: str = None, file: str = None):
        self.condition = None
        self.content = content
        self.file = file
    def execute(self, context: Context, messages = None, run_condition: RunCondition = RunCondition.ALWAYS):
        
        if not should_execute(context, run_condition):       
            return messages, None
        
        if not messages:
            messages = []
        
        if self.content is not None:
            content = self.content
        else:
            base_path = context.content_path + "/" if context.content_path is not None else ""
            prompt = thoughts.interfaces.prompting.load_template(base_path + self.file)
            content = prompt["content"]

        prompt_message = HumanMessage(content=content)
        messages.append(prompt_message)
        return messages, None

    @classmethod
    def parse_json(cls, json_snippet, config):
        moniker = get_first_moniker(json_snippet, cls.monikers)
        content = json_snippet.get(moniker, None)
        return cls(content=content)

class StartInstruction(Instruction):
    monikers = ["StartInstruction"]
    def execute(self, context: Context, messages=None):
        return super().execute(context, messages, run_condition=RunCondition.START)
    
class ContinueInstruction(Instruction):
    monikers = ["ContinueInstruction"]
    def execute(self, context: Context, messages=None):
        return super().execute(context, messages, run_condition=RunCondition.CONTINUATION)

class MessagesBatchAdder(Operation):
    def __init__(self, batch_size: int = 4, exclude_ids: list = [], allow_partial_batch: bool = False):
        self.batch_size = batch_size
        self.exclude_ids = exclude_ids
        self.allow_partial_batch = allow_partial_batch
        self.current_batch = 0

    def execute(self, context: Context, messages: list = []):

        # Exclude messages based on message_id property
        new_messages = [(i, msg) for i, msg in enumerate(context.messages) if msg.message_id not in self.exclude_ids]

        if not new_messages:
            return None, False

        # Calculate the starting index for the current batch
        start_idx = self.current_batch * self.batch_size
        end_idx = start_idx + self.batch_size

        # Get the current batch of messages
        batch = new_messages[start_idx:end_idx]

        if not batch:
            return messages, False

        indices, batch_messages = zip(*batch) if batch else ([], [])

        if not self.allow_partial_batch and len(batch_messages) < self.batch_size:
            return [], False

        messages.extend(batch_messages)

        # Increment current batch index
        self.current_batch += 1

        # If we have processed all batches, reset for next time
        if end_idx >= len(new_messages):
            self.current_batch = 0
            return messages, False
        
        return messages, True

class ContextItemAppender(Operation):
    """
    Appends additional content to the last message in a given list based on 
    configuration and the system's context.

    Behavior:
        - Adds predefined or dynamically loaded template content if specified.
        - Includes additional context-specific data or items, optionally formatted 
          and prefixed with a title.
        - Returns the updated messages with the appended content.

    Args:
        context (Context): The context containing configuration and data for
            retrieving or formatting content.
        messages (list, optional): A list of message objects to modify. Defaults to None.

    Returns:
        tuple:
            - The modified list of messages.
            - None (placeholder for additional data).
    """
     
    def __init__(self, prompt_name: str = None, item_key: str = None, items = None, title = None):
        self.condition = None
        self.prompt_name = prompt_name
        self.item_key = item_key
        self.items = items
        self.title = title

    def execute(self, context: Context, messages = None):
        # get the info we need, or if not available then exit
        prompt_message = messages[-1] if messages else None
        if not prompt_message:
            return messages, None
        
        # load the static content
        if self.prompt_name:
            base_path = context.content_path + "/" if context.content_path is not None else ""
            prompt = thoughts.interfaces.prompting.load_template(base_path + self.prompt_name)
            prompt_message.content += prompt["content"]
        
        item = None
        if self.item_key is not None:
            item = context.get_item(self.item_key)
            if item and "content" in item:
                item = item["content"]
        elif self.items is not None:
            item = self.items

        if item is not None:
            item_text = context.format_value(item)
            if self.title is not None:
                item_text = self.title + ":\n" + item_text
            prompt_message.content += item_text + "\n\n"

        # return the final
        return messages, None

# class StaticPromptLoader(Operation):
#     def __init__(self, prompt_name: str, insert_item: str = None):
#         self.condition = None
#         self.prompt_name = prompt_name
#         self.insert_item = insert_item

#     def parse_template(self, context: Context, template: str):
#         try:
#             parsed_text = template.format_map(DictFormatter(context.items))
#         except KeyError as e:
#             raise ValueError(f"Missing key in context items: {e}")
#         return parsed_text

#     def execute(self, context: Context, message = None):
#         base_path = context.prompt_path + "/" if context.prompt_path is not None else ""
#         prompt = thoughts.interfaces.prompting.load_template(base_path + self.prompt_name)
#         prompt["content"] = self.parse_template(context, prompt["content"])
#         return prompt, None

# class StaticContentLoader(Operation):
#     def __init__(self, content = None, title: str = None, instructions: str = None):
#         self.condition = None
#         self.content = content
#         self.title = title
#         self.instructions = instructions
#     def execute(self, context: Context, message = None):
#         if self.content is None:
#             return None, None
#         if type(self.content) is list:
#             return {"content": "\n".join(self.content), "title": self.title, "instructions": self.instructions }, None
#         elif type(self.content) is dict:
#             return {"content": str(self.content), "title": self.title,  "instructions": self.instructions}, None

class PromptConstructor(Operation):
    def __init__(self, operations: list):
        self.condition = None
        self.operations = operations
    def execute(self, context: Context, message = None):
        operation: Operation
        messages = []
        for operation in self.operations:
            if type(operation) is str:
                operation = IncludeContext(content=operation)
            messages, control = operation.execute(context, messages)
        return messages, None
    @classmethod
    def parse_json(cls, json_snippet, config):
        ops = json_snippet
        operations = []

        moniker_mapping = create_moniker_mapping(Operation)

        for op in ops:
            operation = None
            
            if isinstance(op, str):
                operation = IncludeContext(title=None, content=op)
            else:
                moniker = get_first_moniker(op, moniker_mapping.keys())
                operation_class = moniker_mapping.get(moniker)
                if operation_class:
                    operation = operation_class.parse_json(op, config)

            # if type(op) is str:
            #     operation = IncludeContext(title=None, content=op)
            
            # elif "Role" in op:
            #     operation = Role.parse_json(op, config)
            # elif "ContinueRole" in op:
            #     operation = ContinueRole.parse_json(op, config)
            # elif "StartRole" in op:
            #     operation = StartRole.parse_json(op, config)

            # elif "Context" in op or "InlcudeContext" in op:
            #     operation = IncludeContext.parse_json(op, config)
            # elif "ContinueContext" in op:
            #     operation = ContinueContext.parse_json(op, config)
            # elif "StartContext" in op:
            #     operation = StartContext.parse_json(op, config)

            # elif "Item" in op or "IncludeItem" in op:
            #     operation = IncludeItem.parse_json(op, config)
            # elif "ContinueItem" in op:
            #     operation = ContinueItem.parse_json(op, config)
            # elif "StartItem" in op:
            #     operation = StartItem.parse_json(op, config)

            # elif "File" in op or "IncludeFile" in op:
            #     operation = IncludeFile.parse_json(op, config)
            # elif "ContinueFile" in op:
            #     operation = ContinueFile.parse_json(op, config)
            # elif "StartFile" in op:
            #     operation = StartFile.parse_json(op, config)

            # elif "History" in op or "IncludeHistory" in op:
            #     operation = IncludeHistory.parse_json(op, config)
            # elif "ContinueHistory" in op:
            #     operation = ContinueHistory.parse_json(op, config)
            # elif "StartHistory" in op:
            #     operation = StartHistory.parse_json(op, config)

            # elif "Instruction" in op:
            #     operation = StartInstruction.parse_json(op, config)
            # elif "ContinueInstruction" in op:
            #     operation = ContinueInstruction.parse_json(op, config)
            # elif "StartInstruction" in op:
            #     operation = StartInstruction.parse_json(op, config)
                
            operations.append(operation)
        return cls(operations=operations)
          
class PromptRunner(Operation):
    """
    Runs a prompt against an LLM with customizable behavior.

    - **Frequency of Execution**: Use `run_every` to specify how often the prompt runs (e.g., `2` to run every other call). Leave it as the default to run on every invocation.

    - **Prompt Construction**: Provide a `prompt_constructor` for a custom pipeline to build prompts. If omitted, the `prompt_name` is used as a single system prompt.

    - **Chat History**: Set `num_chat_history` to include recent messages from the context in the prompt. Defaults to `0` for no history.

    - **Streaming**: Enable `stream` (default) to receive a streaming response from the LLM or set it to `False` for a single complete response.

    - **History Management**: Use `append_history` to control whether input and output messages are saved to the context. Defaults to `True`.

    - **Execution**: Call `execute` with a `Context` object and an optional message. The method builds the prompt, adds context messages, sends it to the LLM, and returns the generated response.

    This class is ideal for creating dynamic and configurable LLM interactions, supporting both simple and advanced workflows.
    """

    def __init__(
        self,
        prompt_name: str = None,
        prompt_constructor: PromptConstructor = None,
        num_chat_history=0,
        stream=True,
        run_every: int = 1,
        append_history: bool = False, 
        run_as_message: bool = False, 
        append_last_message: bool = False, 
        store_into: str = "#temp", 
        format_as: str = None, 
        temperature: float = 0.8,
        console: bool = False
    ):
        self.prompt_name = prompt_name
        self.num_chat_history = num_chat_history
        self.prompt_constructor = prompt_constructor
        self.condition = None
        self.stream = stream
        self.run_every = run_every
        self.runs_since_last = 0
        self.append_history = append_history
        self.append_last_message = append_last_message
        self.run_as_message = run_as_message
        self.store_into = store_into
        self.format_as = format_as
        self.temperature = temperature
        self.console = console

    def execute(self, context: Context, message = None):

        context.logger("PromptRunner")

        # check if 'run every' is set and need to wait
        self.runs_since_last += 1
        if self.runs_since_last < self.run_every:
            return None, None
        self.runs_since_last = 0
        
        # construct the main (system) prompt
        if self.prompt_constructor is None:
            prompt_starter = Role(self.prompt_name)
            prompt_constructor = PromptConstructor([prompt_starter])
        else:
            prompt_constructor = self.prompt_constructor
        messages, control = prompt_constructor.execute(context, message)

        # grab the last several messages from the context
        # and append it to the start
        history_messages = context.peek_messages(self.num_chat_history)
        messages.extend(history_messages)

        # append the incoming message if there is one
        if self.append_last_message and message is not None:
            messages.append(message)

        # record incoming message to context history
        if self.append_history:
            context.push_message(message)
           
        # run the prompt against the LLM
        if not self.format_as:
            ai_message = context.llm.invoke(messages, self.stream, temperature=self.temperature)
        elif self.format_as == "json":
            # API requires the word 'json' to be included in the messages
            last_message: PromptMessage = messages[-1]
            last_message.content = last_message.content + "\nFormat as JSON."
            messages[-1] = last_message
            ai_message = context.llm.invoke(messages, self.stream, json=True, temperature=self.temperature)

        # append to history if needed
        if self.append_history:
            context.push_message(ai_message)
        
        context.set_item(self.store_into, ai_message)

        if self.console:
            ConsoleWriter(text=ai_message.content).execute(context)

        # return the message generated
        return ai_message, None
    
    @classmethod
    def parse_json(cls, json_snippet, config):

        num_chat_history = json_snippet.get("num_chat_history", 0)
        run_every = json_snippet.get("run_every", 1)
        append_history = json_snippet.get("append_history", False)
        append_last_message = json_snippet.get("append_last_message", False)
        store_into = json_snippet.get("into", "#temp")
        format_as = json_snippet.get("format", None)
        temperature = json_snippet.get("temp", None)
        write_to_console = json_snippet.get("console", False)

        nodes = []

        def add_nodes(items, start_node_defined):
            for item in items:
                if type(item) is dict and "instruct" in item or "MessageAppender" in item:
                    op = Instruction.parse_json(item, config)
                # elif type(item) is dict and "remember" in item or "MemoryKeeper" in item:
                #     op = MemoryKeeper.parse_json(item, config)
                # elif type(item) is dict and "recall" in item or "ContextMemoryAppender" in item:
                #     op = ContextMemoryAppender.parse_json(item, config)
                elif type(item) is dict and "start" in item or "PromptStarter" in item:
                    nodes.clear()
                    op = Role.parse_json(item, config)
                    start_node_defined = True
                elif type(item) is dict and "history" in item or "MessagesLoader" in item:
                    op = IncludeHistory.parse_json(item, config)
                elif not start_node_defined:
                    op = Role.parse_json(item, config)
                    start_node_defined = True
                else:
                    op = IncludeContext.parse_json(item, config)
                nodes.append(op)
            return start_node_defined

        start_node_defined = add_nodes(config.get("system", []), False)

        main_key = (
            "think" if "think" in json_snippet else
            "communicate" if "communicate" in json_snippet else
            "remember" if "remember" in json_snippet else
            "PromptRunner" if "PromptRunner" in json_snippet else
            None
    )
        add_nodes(json_snippet.get(main_key, []), start_node_defined)

        prompt_constructor = PromptConstructor(nodes)
        return cls(prompt_constructor=prompt_constructor, 
                   num_chat_history=num_chat_history, run_every=run_every, 
                   append_history=append_history, append_last_message=append_last_message, 
                   store_into=store_into, format_as=format_as, temperature=temperature, console=write_to_console)
    
    # @classmethod
    # def parse_json(cls, json_snippet, config):

    #     num_chat_history = json_snippet.get("num_chat_history", 0)

    #     start_node_defined = False
    #     nodes = []

    #     if "system" in config:
    #         for item in config["system"]:
    #             if start_node_defined == False:
    #                 op = PromptStarter.parse_json(item, config)
    #                 start_node_defined = True
    #             else:
    #                 op = PromptAppender.parse_json(item, config)
    #             nodes.append(op)

    #     for item in json_snippet["think"]:
    #         if start_node_defined == False:
    #             op = PromptStarter.parse_json(item, config)
    #             start_node_defined = True
    #         else:
    #             op = PromptAppender.parse_json(item, config)
    #         nodes.append(op)
            
    #     prompt_constructor = PromptConstructor(nodes)
    #     return cls(prompt_constructor=prompt_constructor, num_chat_history=num_chat_history)
    
# class PromptRunner1(Operation):
#     def __init__(
#         self,
#         prompt_name: str = None,
#         prompt_constructor: PromptConstructor = None,
#         num_chat_history=0,
#         stream=True,
#         run_every: int = 1,
#         append_history: bool =True, 
#         run_as_message: bool = False
#     ):
#         self.prompt_name = prompt_name
#         self.num_chat_history = num_chat_history
#         self.prompt_constructor = prompt_constructor
#         self.condition = None
#         self.stream = stream
#         self.run_every = run_every
#         self.runs_since_last = 0
#         self.append_history = append_history
#         self.run_as_message = run_as_message

#     def execute(self, context: Context, message = None):
#         # message = context.peek()

#         self.runs_since_last += 1
#         if self.runs_since_last < self.run_every:
#             return None, None
#         self.runs_since_last = 0
        
#         if self.prompt_constructor is None:
#             static_prompt_loader = StaticPromptLoader(self.prompt_name)
#             prompt_constructor = PromptConstructor([static_prompt_loader])
#         else:
#             prompt_constructor = self.prompt_constructor
#         prompt, control = prompt_constructor.execute(context)

#         message_history = context.peek_messages(self.num_chat_history)
#         prompt["messages"] = message_history

#         if message is not None:
#             if type(message) is list:
#                 prompt["messages"].extend(message)
#             else:
#                 prompt["messages"].append(message)

#         if self.run_as_message:
#             new_message = HumanMessage(content=prompt["content"])
#             prompt["content"] = "You are a helpful AI assistant."
#             prompt["messages"].append(new_message)

#         ai_message = context.llm.respond(prompt, self.stream)
        
#         if self.append_history:
#             context.push_message(ai_message)
        
#         return ai_message, None
    
# class PromptResumer(Operation):
#     def __init__(
#         self,
#         start_prompt_name,
#         continue_prompt_name,
#         start_if_no_messages=True,
#         add_to_chat_history=True,
#     ):
#         self.start_prompt_name = start_prompt_name
#         self.continue_prompt_name = continue_prompt_name
#         self.start_if_no_messages = start_if_no_messages
#         self.add_to_chat_history = add_to_chat_history

    # def execute(self, context: Context):

    #     context.memory.load_previous_messages()
    #     last_messages = context.memory.get_chat_history(1)
    #     last_message = last_messages[0] if len(last_messages) > 0 else None
    #     ai_message = last_message if last_message is not None and last_message["speaker"] == "AI" else None
    #     human_message = last_message if last_message is not None and last_message["speaker"] == "Human" else None

    #     if ai_message is None and human_message is None and self.start_if_no_messages:
    #         prompt = interfaces.prompting.build_prompt(self.start_prompt_name, context.memory)
    #         ai_message = context.llm.respond(prompt)
    #         if self.add_to_chat_history:
    #             context.memory.add_chat_history(ai_message)
    #             context.push(ai_message)
    #         return ai_message, False

    #     elif ai_message is not None:
    #         return ai_message, True

    #     elif human_message is not None:
    #         prompt = interfaces.prompting.build_prompt(self.continue_prompt_name, context.memory, human_message)
    #         ai_message = context.llm.respond(prompt)
    #         if self.add_to_chat_history:
    #             context.memory.add_chat_history(ai_message)
    #             context.push(ai_message)
    #         return ai_message, False

    #     return None, False

    # def execute(self, context: Context):
    #     context.memory.load_previous_messages()
    #     last_messages = context.memory.get_chat_history(1)
    #     last_message = last_messages[0] if last_messages else None

    #     if last_message:
    #         if last_message["speaker"] == "AI":
    #             return last_message, True
    #         elif last_message["speaker"] == "Human":
    #             prompt_name = self.continue_prompt_name
    #             human_message = last_message
    #     else:
    #         if self.start_if_no_messages:
    #             prompt_name = self.start_prompt_name
    #             human_message = None
    #         else:
    #             return None, False

    #     prompt = thoughts.interfaces.prompting.build_prompt(
    #         prompt_name, context.memory, human_message
    #     )
    #     ai_message = context.llm.respond(prompt)
    #     if self.add_to_chat_history:
    #         context.memory.add_chat_history(ai_message)
    #         context.push_message(ai_message)

    #     return ai_message, None
