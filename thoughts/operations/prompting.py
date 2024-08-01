from thoughts.interfaces.messaging import AIMessage, HumanMessage, PromptMessage, SystemMessage
from thoughts.operations.core import Operation
import thoughts.interfaces.prompting
from thoughts.engine import Context

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

class PromptStarter(Operation):
    def __init__(self, role: str = "system", prompt_name: str = None, content: str = None):
        self.condition = None
        self.role = role
        self.prompt_name = prompt_name
        self.content = content
    def execute(self, context: Context, messages = None):
        if self.content is not None:
            content = self.content
        else:
            base_path = context.prompt_path + "/" if context.prompt_path is not None else ""
            prompt = thoughts.interfaces.prompting.load_template(base_path + self.prompt_name)
            content = prompt["content"]

        if messages is None:
            messages = []

        if self.role == "system":
            messages.append(SystemMessage(content=content))
        elif self.role == "ai":
            messages.append(AIMessage(content=content))
        elif self.role == "human":
            messages.append(HumanMessage(content=content))
        
        return messages, None
    
class PromptAppender(Operation):
    def __init__(self, prompt_name: str = None, content: str = None):
        self.condition = None
        self.prompt_name = prompt_name
        self.content = content
    def execute(self, context: Context, messages = None):
        if not messages:
            return messages, None
        
        prompt_message: PromptMessage = messages[-1] if messages else None
    
        if self.content is not None:
            content = self.content
        else:
            base_path = context.prompt_path + "/" if context.prompt_path is not None else ""
            prompt = thoughts.interfaces.prompting.load_template(base_path + self.prompt_name)
            content = prompt["content"]

        prompt_message.content += content
        return messages, None

class MessagesLoader(Operation):
    def __init__(self, num_messages: int = 4):
        self.condition = None
        self.num_messages = num_messages
    def execute(self, context: Context, messages = None):
        message_history = context.peek_messages(self.num_messages)
        if messages is None:
            messages = []
        messages.extend(message_history)
        return messages, None
    
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


# class MessagesBatchAdder(Operation):
#     def __init__(self, batch_size: int = 4, exclude_ids: list = []):
#         self.batch_size = batch_size
#         self.exclude_ids = exclude_ids
#         self.current_batch = 0
#     def execute(self, context: Context, messages: list = None):
#         # Find the next batch of messages to process
#         new_messages = [(i, msg) for i, msg in enumerate(context.messages) if i not in self.exclude_ids]
#         if not new_messages:
#             return None, None

#         if len(new_messages) < self.batch_size:
#             return None, None
        
#         batches = [new_messages[i:i + self.batch_size] for i in range(0, len(new_messages), self.batch_size)]
#         batch = batches[self.current_batch]          
#         indices, batch_messages = zip(*batch)
        
#         messages.extend(batch_messages)
#         self.current_batch += 1
#         return messages, None

class ContextItemAppender(Operation):
    
    def __init__(self, prompt_name: str, item_key: str):
        self.condition = None
        self.prompt_name = prompt_name
        self.item_key = item_key

    def execute(self, context: Context, messages = None):

        # get the info we need, or if not available then exit
        prompt_message: PromptMessage = messages[-1] if messages else None
        item = context.get_item(self.item_key)
        
        if prompt_message is None or item is None:
            return messages, None
        
        if "content" in item:
            item = item["content"]
            
        # load the static content
        base_path = context.prompt_path + "/" if context.prompt_path is not None else ""
        prompt = thoughts.interfaces.prompting.load_template(base_path + self.prompt_name)
        prompt_message.content += prompt["content"]
        
        # load the content item content
        item_text = context.format_value(item)
        prompt_message.content += item_text
        
        # return the final
        return messages, None

class StaticPromptLoader(Operation):
    def __init__(self, prompt_name: str, insert_item: str = None):
        self.condition = None
        self.prompt_name = prompt_name
        self.insert_item = insert_item

    def parse_template(self, context: Context, template: str):
        try:
            parsed_text = template.format_map(DictFormatter(context.items))
        except KeyError as e:
            raise ValueError(f"Missing key in context items: {e}")
        return parsed_text

    def execute(self, context: Context):
        base_path = context.prompt_path + "/" if context.prompt_path is not None else ""
        prompt = thoughts.interfaces.prompting.load_template(base_path + self.prompt_name)
        prompt["content"] = self.parse_template(context, prompt["content"])
        return prompt, None

class StaticContentLoader(Operation):
    def __init__(self, content = None, title: str = None, instructions: str = None):
        self.condition = None
        self.content = content
        self.title = title
        self.instructions = instructions
    def execute(self, context: Context, message = None):
        if self.content is None:
            return None, None
        if type(self.content) is list:
            return {"content": "\n".join(self.content), "title": self.title, "instructions": self.instructions }, None
        elif type(self.content) is dict:
            return {"content": str(self.content), "title": self.title,  "instructions": self.instructions}, None
    
# class MessageHistoryAdder(Operation):
#     def __init__(self, num_messages: int = 0):
#         self.num_messages = num_messages
#     def execute(self, context: Context):
#         prompt = context.get("prompt")
#         messages = context.peek(self.num_messages)
#         prompt["messages"].extend(messages)

class PromptConstructor(Operation):
    def __init__(self, operations: list):
        self.condition = None
        self.operations = operations
    def execute(self, context: Context):
        operation: Operation
        messages = []
        for operation in self.operations:
            messages, control = operation.execute(context, messages)
        return messages, None
    
class PromptConstructor1(Operation):
    def __init__(self, operations: list):
        self.condition = None
        self.operations = operations

    def execute(self, context: Context):
        operation: Operation
        prompt_parts = []
        for operation in self.operations:
            prompt, control = operation.execute(context)
            if prompt is None:
                continue
            prompt_parts.append(prompt)

        prompt_text: str = ""
        for prompt_part in prompt_parts:
            title = prompt_part["title"] + ":\n" if "title" in prompt_part and prompt_part["title"] is not None else ""
            instructions = prompt_part["instructions"] + "\n" if "instructions" in prompt_part else ""
            # prompt_part_text = "".join(prompt_part["content"])

            prompt_part_text = prompt_part["content"]
            prompt_text += "\n" + instructions + title + prompt_part_text
            
        prompt_text = str.strip(prompt_text)

        prompt = {"content": prompt_text, "messages": []}
        context.set_item("prompt", prompt)

        return prompt, None
        
class PromptRunner(Operation):
    def __init__(
        self,
        prompt_name: str = None,
        prompt_constructor: PromptConstructor = None,
        num_chat_history=0,
        stream=True,
        run_every: int = 1,
        append_history: bool =True, 
        run_as_message: bool = False
    ):
        self.prompt_name = prompt_name
        self.num_chat_history = num_chat_history
        self.prompt_constructor = prompt_constructor
        self.condition = None
        self.stream = stream
        self.run_every = run_every
        self.runs_since_last = 0
        self.append_history = append_history
        self.run_as_message = run_as_message

    def execute(self, context: Context, message = None):
        # message = context.peek()

        self.runs_since_last += 1
        if self.runs_since_last < self.run_every:
            return None, None
        self.runs_since_last = 0
        
        if type(message) is list:
            messages = message
        else:
            if self.prompt_constructor is None:
                static_prompt_loader = StaticPromptLoader(self.prompt_name)
                prompt_constructor = PromptConstructor([static_prompt_loader])
            else:
                prompt_constructor = self.prompt_constructor
                messages, control = prompt_constructor.execute(context)

            if message is not None:
                messages.append(message)
            
        ai_message = context.llm.respond(messages, self.stream)
        
        if self.append_history:
            context.push_message(ai_message)
        
        return ai_message, None

class PromptRunner1(Operation):
    def __init__(
        self,
        prompt_name: str = None,
        prompt_constructor: PromptConstructor = None,
        num_chat_history=0,
        stream=True,
        run_every: int = 1,
        append_history: bool =True, 
        run_as_message: bool = False
    ):
        self.prompt_name = prompt_name
        self.num_chat_history = num_chat_history
        self.prompt_constructor = prompt_constructor
        self.condition = None
        self.stream = stream
        self.run_every = run_every
        self.runs_since_last = 0
        self.append_history = append_history
        self.run_as_message = run_as_message

    def execute(self, context: Context, message = None):
        # message = context.peek()

        self.runs_since_last += 1
        if self.runs_since_last < self.run_every:
            return None, None
        self.runs_since_last = 0
        
        if self.prompt_constructor is None:
            static_prompt_loader = StaticPromptLoader(self.prompt_name)
            prompt_constructor = PromptConstructor([static_prompt_loader])
        else:
            prompt_constructor = self.prompt_constructor
        prompt, control = prompt_constructor.execute(context)

        message_history = context.peek_messages(self.num_chat_history)
        prompt["messages"] = message_history

        if message is not None:
            if type(message) is list:
                prompt["messages"].extend(message)
            else:
                prompt["messages"].append(message)

        if self.run_as_message:
            new_message = HumanMessage(content=prompt["content"])
            prompt["content"] = "You are a helpful AI assistant."
            prompt["messages"].append(new_message)

        ai_message = context.llm.respond(prompt, self.stream)
        
        if self.append_history:
            context.push_message(ai_message)
        
        return ai_message, None
    
class PromptResumer(Operation):
    def __init__(
        self,
        start_prompt_name,
        continue_prompt_name,
        start_if_no_messages=True,
        add_to_chat_history=True,
    ):
        self.start_prompt_name = start_prompt_name
        self.continue_prompt_name = continue_prompt_name
        self.start_if_no_messages = start_if_no_messages
        self.add_to_chat_history = add_to_chat_history

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

    def execute(self, context: Context):
        context.memory.load_previous_messages()
        last_messages = context.memory.get_chat_history(1)
        last_message = last_messages[0] if last_messages else None

        if last_message:
            if last_message["speaker"] == "AI":
                return last_message, True
            elif last_message["speaker"] == "Human":
                prompt_name = self.continue_prompt_name
                human_message = last_message
        else:
            if self.start_if_no_messages:
                prompt_name = self.start_prompt_name
                human_message = None
            else:
                return None, False

        prompt = thoughts.interfaces.prompting.build_prompt(
            prompt_name, context.memory, human_message
        )
        ai_message = context.llm.respond(prompt)
        if self.add_to_chat_history:
            context.memory.add_chat_history(ai_message)
            context.push_message(ai_message)

        return ai_message, None
