from datetime import datetime
import os
import re
from thoughts.context import Context
from thoughts.interfaces.messaging import PromptMessage, AIMessage, HumanMessage, SystemMessage
from thoughts.operations.core import Operation
# from thoughts.operations.prompting import MessagesBatchAdder, PromptConstructor, PromptRunner, PromptStarter, PromptAppender
from thoughts.operations.prompting import IncludeContext, IncludeFile, IncludeHistory, IncludeItem, Role, StartInstruction
from thoughts.util import convert_to_list

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
    def __init__(self, prompt_name: str = None, role: str = "system", content: str = "You are a helpful AI assistant."):
        self.condition = None
        self.role = role
        self.prompt_name = prompt_name
        self.content = content
    def execute(self, context: Context, messages = None):
        import thoughts.interfaces.prompting  # Lazy import

        if self.prompt_name is not None:
            base_path = context.content_path + "/" if context.content_path is not None else ""
            prompt = thoughts.interfaces.prompting.load_template(base_path + self.prompt_name)
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
        return cls(content=json_snippet)

class PromptAppender(Operation):
    def __init__(self, prompt_name: str = None, content: str = None):
        self.condition = None
        self.prompt_name = prompt_name
        self.content = content
    def execute(self, context: Context, messages = None):
        import thoughts.interfaces.prompting  # Lazy import

        if not messages:
            return messages, None
        
        prompt_message: PromptMessage = messages[-1] if messages else None
    
        if self.content is not None:
            content = self.content
        else:
            base_path = context.content_path + "/" if context.content_path is not None else ""
            prompt = thoughts.interfaces.prompting.load_template(base_path + self.prompt_name)
            content = prompt["content"]

        prompt_message.content += content
        return messages, None

    @classmethod
    def parse_json(cls, json_snippet, config):
        return cls(content=json_snippet)

class MessageAppender(Operation):
    def __init__(self, prompt_name: str = None, content: str = None):
        self.condition = None
        self.prompt_name = prompt_name
        self.content = content
    def execute(self, context: Context, messages = None):
        import thoughts.interfaces.prompting  # Lazy import

        if not messages:
            messages = []
        
        if self.content is not None:
            content = self.content
        else:
            base_path = context.content_path + "/" if context.content_path is not None else ""
            prompt = thoughts.interfaces.prompting.load_template(base_path + self.prompt_name)
            content = prompt["content"]

        prompt_message = HumanMessage(content=content)
        messages.append(prompt_message)
        return None, None

    @classmethod
    def parse_json(cls, json_snippet, config):
        content=json_snippet["instruct"]
        return cls(content=content)

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
        new_messages = [(i, msg) for i, msg in enumerate(context.messages) if msg.message_id not in self.exclude_ids]

        if not new_messages:
            return None, False

        start_idx = self.current_batch * self.batch_size
        end_idx = start_idx + self.batch_size

        batch = new_messages[start_idx:end_idx]

        if not batch:
            return messages, False

        indices, batch_messages = zip(*batch) if batch else ([], [])

        if not self.allow_partial_batch and len(batch_messages) < self.batch_size:
            return [], False

        messages.extend(batch_messages)

        self.current_batch += 1

        if end_idx >= len(new_messages):
            self.current_batch = 0
            return messages, False
        
        return messages, True

class ContextItemAppender(Operation):
    def __init__(self, prompt_name: str = None, item_key: str = None, items = None, title = None):
        self.condition = None
        self.prompt_name = prompt_name
        self.item_key = item_key
        self.items = items
        self.title = title

    def execute(self, context: Context, messages = None):
        import thoughts.interfaces.prompting  # Lazy import

        prompt_message = messages[-1] if messages else None
        if not prompt_message:
            return messages, None
        
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

        return messages, None

# class PromptConstructor(Operation):
#     def __init__(self, operations: list):
#         self.condition = None
#         self.operations = operations
#     def execute(self, context: Context, message = None):
#         operation: Operation
#         messages = []
#         for operation in self.operations:
#             messages, control = operation.execute(context, messages)
#         return messages, None
          
# class PromptRunner(Operation):
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
#         self.runs_since_last += 1
#         if self.runs_since_last < self.run_every:
#             return None, None
#         self.runs_since_last = 0
        
#         if self.prompt_constructor is None:
#             prompt_starter = PromptStarter(self.prompt_name)
#             prompt_constructor = PromptConstructor([prompt_starter])
#         else:
#             prompt_constructor = self.prompt_constructor
#         messages, control = prompt_constructor.execute(context, message)

#         history_messages = context.peek_messages(self.num_chat_history)
#         messages.extend(history_messages)

#         if message is not None:
#             messages.append(message)

#         if self.append_history:
#             context.push_message(message)
           
#         ai_message = context.llm.invoke(messages, self.stream)
        
#         if self.append_history:
#             context.push_message(ai_message)
        
#         return ai_message, None

#     @classmethod
#     def parse_json(cls, json_snippet, config):
#         num_chat_history = json_snippet.get("num_chat_history", 0)
#         run_every = json_snippet.get("run_every", 1)

#         nodes = []

#         def add_nodes(items, start_node_defined):
#             for item in items:
#                 if "instruct" in item:
#                     op = MessageAppender.parse_json(item, config)
#                 elif "recall" in item:
#                     from thoughts.operations.memory import ContextMemoryAppender  # Lazy import
#                     op = ContextMemoryAppender.parse_json(item, config)
#                 elif not start_node_defined:
#                     op = PromptStarter.parse_json(item, config)
#                     start_node_defined = True
#                 else:
#                     op = PromptAppender.parse_json(item, config)
#                 nodes.append(op)
#             return start_node_defined

#         start_node_defined = add_nodes(config.get("system", []), False)
#         add_nodes(json_snippet.get("think", []), start_node_defined)

#         prompt_constructor = PromptConstructor(nodes)
#         return cls(prompt_constructor=prompt_constructor, num_chat_history=num_chat_history, run_every=run_every)

class RAGContextAdder(Operation):

    def __init__(self, collection_name: str, title: str):
        self.collection_name = collection_name
        self.title = title

    def execute(self, context: Context, message = None):
        from thoughts.operations.prompting import PromptConstructor  # Lazy import

        search_message = message if message is not None else context.get_last_message()
        memories = context.memory.find(self.collection_name, search_message)
        
        prompt = context.get_item("prompt")
        if "context" not in prompt:
            prompt["context"] = []
        
        rag_context = {"context": self.collection_name, "items": memories}
        prompt["context"].append(rag_context)
        
        return rag_context, None
    
class MemoryKeeper(Operation):
    def __init__(self, item_key: str = "", replace: bool = False):
        self.condition = None
        self.item_key = item_key
        self.replace = replace
    def execute(self, context: Context, message = None):
        if message is not None:
            if self.replace:
                context.set_item(self.item_key, message.content)
            else:
                context.append_item(self.item_key, message.content)
        return None, None
    @classmethod
    def parse_json(cls, json_snippet, config):
        moniker = "into" if "into" in json_snippet else "MemoryKeeper"
        key = json_snippet[moniker]
        replace = json_snippet.get("replace", False)
        return cls(item_key=key, replace=replace)
    
class MemoryRetriever(Operation):
    def __init__(self, key: str, title: str, instructions: str = None):
        self.key = key
        self.title = title
        self.instructions = instructions
    def execute(self, context: Context, message = None):
        items = context.get_item(self.key)
        if items is None:
            return None, None
        return items, None
    
class ContextMemoryAppender(Operation):
    def __init__(self, key: str, title: str = None):
        self.condition = None
        self.key = key
        self.title = title
    def execute(self, context: Context, messages = None):
        if not messages:
            return messages, None
        content = context.get_item(self.key)
        
        if content is None:
            return messages, None
        
        if type(content) is list:
            content = "\n".join(content)
        elif isinstance(content, PromptMessage):
            content = "\n\n" + content.content

        prompt_message: PromptMessage = messages[-1] if messages else None
        prompt_message.content += self.title + ":\n" + content if self.title is not None else content
        return messages, None
    @classmethod
    def parse_json(cls, json_snippet, config):
        moniker = "recall" if "recall" in json_snippet else "ContextMemoryAppender"
        key = json_snippet[moniker]
        title = json_snippet.get("as", None)
        return cls(key=key, title=title)
    
def split_numbered_list(text):
    """
    Splits the text from an LLM response into a list of numbered items.
    A new item starts with a number at the beginning of a line.

    Args:
        text (str): The input text containing a numbered list.

    Returns:
        list: A list of strings, each representing a numbered item.
    """
    # Use regex to find lines starting with a number followed by a period or parenthesis
    pattern = r"(?m)^\d+\."
    matches = re.split(pattern, text)

    # Clean up the results and ignore the empty first split if it exists
    items = [item.strip() for item in matches if item.strip()]

    # Re-prepend the numbering for each item to ensure correctness
    return [f"{i+1}. {item}" for i, item in enumerate(items)]

class TextSplitter(Operation):
    def __init__(self, key: str, delimiter: str = "\n", store_into: str = None):
        self.key = key
        self.delimiter = delimiter
        self.condition = None
        self.store_into = store_into
    def execute(self, context: Context, message = None):
        text = context.get_item(self.key)
        if isinstance(text, PromptMessage):
            text = text.content
        items = split_numbered_list(text)
        # items = text.split(self.delimiter)
        # items = [item for item in items if len(item) > 0]
        context.set_item(self.store_into, items)
        return items, None
    @classmethod
    def parse_json(cls, json_snippet, config):
        key = json_snippet["TextSplitter"]
        delimiter = json_snippet.get("delimiter", "\n")
        store_into = json_snippet.get("into", "#temp")
        return cls(key=key, delimiter=delimiter, store_into=store_into)
    
class MessagesSummarizer(Operation):
    
    def __init__(self, prompt_name: str = "", batch_size: int = 0, store_into: str = None, allow_partial_batch=True):
        self.condition = None
        self.prompt_name = prompt_name
        self.batch_size = batch_size
        self.store_into = store_into
        self.allow_partial_batch = allow_partial_batch

    def execute(self, context: Context, message = None):

        # Load existing summaries and processed message indices if the file exists
        data = context.get_item(self.store_into)
        if data is None:
            data = {"content": [], "ids": set()}
        else:
            data = {"content": data["content"], "ids": set(data["ids"])}
        
        summaries: list = data.get("content", [])
        processed_ids: set = data.get("ids", set())

        loop: bool = True
        while loop:

            messages, control = PromptStarter(
            content="You are a helpful AI assistant.").execute(context)

            # will keep adding the next set of messages in batch to the messages
            messages, loop = MessagesBatchAdder(
                self.batch_size, exclude_ids=processed_ids, 
                allow_partial_batch=self.allow_partial_batch).execute(context, messages)

            if not messages or len(messages) == 0:
                continue

            # if loop = False, continue processing the last batch of messages (last time through)!

            messages, control = PromptStarter(self.prompt_name, role="human").execute(context, messages)

            summary, control = PromptRunner(
            stream=False, append_history=False).execute(context, messages)

            summaries.append(summary.content)

            indices = [message.message_id for message in messages]
            processed_ids.update(indices)

        # Save the updated summaries and processed indices to the JSON file
        result = {"content": summaries, "ids": list(processed_ids)}
        context.set_item(self.store_into, result)
        return result, None

class InformationExtractor(Operation):

    def __init__(self, extractor_prompt: str):
        self.extractor_prompt = extractor_prompt

    def _extract_info(self, context: Context, content):

        extractor_persona = PromptStarter(self.extractor_prompt)
        extractor_content = PromptAppender(content=content)
        extractor = PromptConstructor([extractor_persona, extractor_content])

        runner = PromptRunner(prompt_constructor=extractor, run_as_message=True)
        conclusions, control = runner.execute(context)

        return conclusions

    def execute(self, context: Context, message = None):

        # check if already ran
        # todo - set a switch to force this to be recreated
        conclusions = context.get_item(self.extractor_prompt, None)
        if conclusions is not None:
            return conclusions, None
        
        content = context.get_item("summary")

        extractor_persona = PromptStarter(self.extractor_prompt)
        extractor_content = PromptAppender(content=content)
        extractor = PromptConstructor([extractor_persona, extractor_content])

        runner = PromptRunner(prompt_constructor=extractor, run_as_message=True)
        conclusions, control = runner.execute(context)

        context.set_item(self.extractor_prompt, conclusions.content)
        return conclusions, None
    
class SessionIterator(Operation):
    def __init__(self, operations: list, num_previous: int = None):
        self.operations = operations
        self.num_previous = num_previous

    def _get_last_n_folders(self, directory, n):
        # Get a list of all folders in the directory
        all_folders = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]

        # Filter out folders that don't match the yyyy-mm-dd format
        valid_folders = []
        for folder in all_folders:
            try:
                datetime.strptime(folder, '%Y-%m-%d')
                valid_folders.append(folder)
            except ValueError:
                continue

        # Sort the folders in reverse chronological order
        valid_folders.sort(reverse=True)

        # Return the last N folders
        if n is None:
            return valid_folders

        return valid_folders[:n]
    
    def execute(self, context: Context, message = None):
        folders = self._get_last_n_folders("memory/sessions", self.num_previous)
        results = []
        for folder in folders:
            session_id = folder

            print("Extracting", session_id, "...")

            # execution context is a mashup of the persisted session and the session passed in
            execution_context = Context(llm=context.llm, memory=context.memory, 
                                        content_path=context.content_path, session_id=session_id, persist_session=context.persist_session)
            
            operation: Operation = None
            for operation in self.operations:
                result, control = operation.execute(execution_context, message)
                results.append(result)

        return results, None
