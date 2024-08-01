import json
import os
import uuid
from thoughts.interfaces.llm import LLM
from thoughts.interfaces.memory import Memory, MemoryModule
from thoughts.interfaces.messaging import AIMessage, HumanMessage, PromptMessage
from thoughts.operations.core import Operation
from thoughts import unification

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return super().default(obj)

class Context:

    def __init__(self, llm: LLM = None, memory: Memory = None, prompt_path: str = None, session_id: str = None, persist_session: bool = True):
        self.items = {}
        self.llm = llm if llm is not None else LLM()
        self.memory = memory if memory is not None else Memory()
        self.messages = []
        self.session_id = session_id if session_id is not None else str(uuid.uuid4())
        self.memory_module = MemoryModule()
        self.logs = []
        
        session_path = "memory/sessions/" + self.session_id
        if os.path.exists(session_path):
            self.load()

        # run these after the load to override with the values passed in
        self.prompt_path = prompt_path
        self.persist_session = persist_session

    def object_hook(self, data):
        if '__class__' in data:
            class_name = data.pop('__class__')
            if class_name == 'AIMessage':
                return AIMessage.from_dict(data)
            elif class_name == 'HumanMessage':
                return HumanMessage.from_dict(data)
        return data

    def persist(self, persist_changes: bool = True, key: str = ""):
        if self.persist_session == False or persist_changes == False:
            return
        
        # save the manifest to the root
        manifest = {"prompt-path": self.prompt_path, "persist-session": self.persist_session}
        directory_path = "memory/sessions/" + self.session_id
        os.makedirs(directory_path, exist_ok=True)
        with open(os.path.join(directory_path, "manifest.json"), "w") as f:
            json.dump(manifest, f, indent=4)

        # save the items as individual files
        directory_path = "memory/sessions/" + self.session_id + "/items"
        os.makedirs(directory_path, exist_ok=True)
        if key == "":
            with open(os.path.join(directory_path, "items.json"), "w") as f:
                json.dump(self.items, f, indent=4, cls=CustomEncoder)
        else:
            with open(os.path.join(directory_path, key + ".json"), "w") as f:
                item = {key: self.items[key]}
                json.dump(item, f, indent=4, cls=CustomEncoder)
        
        # messages are saved as they are appended

    def read_manifest(self):
        directory_path = "memory/sessions/" + self.session_id
        with open(os.path.join(directory_path, "manifest.json"), "r") as f:
            manifest = json.load(f)
        self.prompt_path = manifest["prompt-path"]
        self.persist_session = manifest["persist-session"]

    def load(self):
        self.read_manifest()
        self.read_items()
        self.read_messages()

    def read_items(self):
        directory_path = "memory/sessions/" + self.session_id + "/items"
        if not os.path.exists(directory_path):
            print(f"No such directory: {directory_path}")
            return
        
        # Load the combined items.json file if it exists
        items_file_path = os.path.join(directory_path, "items.json")
        if os.path.exists(items_file_path):
            with open(items_file_path, "r") as f:
                self.items = json.load(f, object_hook=self.object_hook)

        # Load individual key-value pair files
        for filename in os.listdir(directory_path):
            if filename.endswith(".json") and filename != "items.json":
                key = filename[:-5]  # remove the .json extension
                file_path = os.path.join(directory_path, filename)
                with open(file_path, "r") as f:
                    item = json.load(f, object_hook=self.object_hook)
                    self.items[key] = item[key]

    def get_item(self, key, default=None):
        return self.items.get(key, default)

    def set_item(self, key, value, persist_changes: bool = True):
        self.items[key] = value
        self.persist(persist_changes, key)

    def append_item(self, key, value, persist_changes: bool = True):
        if key not in self.items:
            self.items[key] = []
        if type(self.items[key]) is not list:
            self.items[key] = [self.items[key]] # listify it
        self.items[key].append(value)
        self.persist(persist_changes, key)

    def update_item(self, key, value, persist_changes: bool = True):
        if key in self.items and isinstance(self.items[key], dict) and isinstance(value, dict):
            self.items[key].update(value)
        else:
            self.items[key] = value
        self.persist(persist_changes, key)

    def clear_messages(self):
        self.messages = []

    def push_message(self, value):
        self.messages.append(value)
        self.log_message(value)

    def pop_message(self):
        self.messages.pop()

    def peek_messages(self, num: int = 1):
        if len(self.messages) == 0 or num == 0:
            return []
        return self.messages[-num:] if num <= len(self.messages) else self.messages
    
    def get_last_message(self) -> PromptMessage:
        return self.messages[-1] if self.messages else None

    def log_message(self, message: PromptMessage):
        if self.persist_session == False:
            return
        directory = "memory/sessions/" + self.session_id + "/messages"
        if not os.path.exists(directory):
            os.makedirs(directory)
        filepath = directory + "/log-" + message.message_id + ".json"
        with open(filepath, "w") as f:
            json.dump(message, f, indent=4, cls=CustomEncoder)

    def read_messages(self):
        directory = "memory/sessions/" + self.session_id + "/messages"
        if not os.path.exists(directory):
            return []

        files = os.listdir(directory)
        json_files = [f for f in files if f.endswith(".json")]

        json_files.sort()
        data = []
        for file in json_files:
            with open(os.path.join(directory, file), "r") as f:
                file_data = json.load(f, object_hook=self.object_hook)
                data.append(file_data)

        self.messages = data

    def format_value(self, value):
        if isinstance(value, list):
            return '\n'.join(str(item) for item in value)
        elif isinstance(value, dict):
            return ', '.join(f"{k}: {v}" for k, v in value.items())
        return value

    def apply_values(self, term, provider):
            
        if (type(term) is dict):
            result = {}
            for key in term.keys():
                if key == "#into" or key == "#append" or key == "#push":
                    if type(term[key] is str):
                        if type(provider) is dict:
                            sub_value = unification.retrieve(term[key], provider)
                            if sub_value is not None:
                                result[key] = sub_value
                    if key not in result:
                        result[key] = term[key]
                elif (key == "#combine"):
                    items_to_combine = term["#combine"]
                    newval = {}
                    for item in items_to_combine:
                        new_item = self.apply_values(item, provider)
                        newval = {**new_item, **newval}
                    # assume combine is a standalone operation
                    # could also merge this will other keys
                    # result[key] = newval
                    return newval
                else:
                    newval = self.apply_values(term[key], provider)
                    result[key] = newval
            return result

        elif (type(term) is list):
            result = []
            for item in term:
                # moved from rule engine, refactor
                newitem = self.apply_values(item, provider) 
                result.append(newitem)
            return result

        elif (type(term) is str):
            if type(provider) is dict:
                term = unification.retrieve(term, provider)
            else:
                term = self.retrieve(term)
            return term

        else:
            return term

    def log(self, text):
        self.logs.append(text)

    def retrieve(self, text):

        if ("$" not in text) and ("?" not in text): return text

        results = []

        # tokens = text.split(' ')
        tokens = unification.tokenize(text)

        for token in tokens:

            if str.startswith(token, "?") or str.startswith(token, "$"):

                parts = token.split('.')
                current_item = None

                for part in parts:
                    if current_item is None: # first portion
                        current_item = self.retrieve_items(part)
                    else:
                        if type(current_item) is dict:
                            if part in current_item: 
                                current_item = current_item[part]
                            else:
                                break
                        else:
                            break # later - determine how to handle lists and other types

                    if current_item is None:
                        current_item = token
                        break 

                results.append(current_item)
            else:

                results.append(token) 

        if len(results) == 0: return None
        if len(results) == 1: return results[0]
        else:
            text = ""
            for result in results: 
                if result == "?" or result == ".":
                    text = text + str(result)
                else:
                    text = text + " " + str(result)
            text = text.strip()
            return text

    def retrieve_items(self, item_name, stop_after_first = False):
        
        results = []

        if item_name in self.items: 
            results.append(self.items[item_name])
            if (stop_after_first): return results[0]
        
        if len(results) == 0: return None
        if len(results) == 1: return results[0]
        else: return results

class Node:
    def __init__(self, name: str, operation: Operation, condition=None):
        self.name = name
        self.operation = operation
        self.condition = condition

    def execute(self, context):
        self.operation.execute(context)  # Pass context to operation

class GraphExecutor:
    def __init__(self, context = None):
        self.nodes = {}
        self.edges = {}
        self.context = context if context is not None else Context()

    def add_node(self, name, operation, condition=None):
        if name in self.nodes:
            raise ValueError(f"Node with name {name} already exists.")
        node = Node(name, operation, condition)
        self.nodes[name] = node
        return node

    def add_edge(self, from_node_name, to_node_name, condition=None):
        if from_node_name not in self.nodes or to_node_name not in self.nodes:
            raise ValueError("Both nodes must exist before adding an edge.")
        if from_node_name not in self.edges:
            self.edges[from_node_name] = []
        self.edges[from_node_name].append((to_node_name, condition))

    def execute(self, start_node_name, context=None):

        if context is not None:
            self.context = context

        if start_node_name not in self.nodes:
            raise ValueError("Start node must exist in the graph.")
        
        current_node: Node = self.nodes[start_node_name]
        while current_node:
            if not current_node.condition or current_node.condition(self.context):
                current_node.execute(self.context)
                # print(f"Output of {current_node.operation}: {context.data}")
            next_node = None
            for node_name, condition in self.edges.get(current_node.name, []):
                node = self.nodes[node_name]
                if condition is None or condition(self.context):
                    next_node = node
                    break
            current_node = next_node

class PipelineExecutor:
    def __init__(self, nodes=[], context = None, loop = False):
        self.nodes = nodes
        self.context = context if context is not None else Context()
        self.loop = loop

    def execute(self, context: Context = None, message = None):

        if context is not None:
            self.context = context
        
        if self.nodes is None:
            return None, None
        
        result = message
        idx = 0

        results = []

        while True:
            
            # detect if done or need to loop back to the first node
            if idx >= len(self.nodes):
                # # persist the context after each run
                # self.context.persist()
                if self.loop:
                    idx = 0
                else:
                    break
            
            # run the next operation
            current_node: Node = self.nodes[idx]
            if not current_node.condition or current_node.condition(self.context):
                result, control = current_node.execute(self.context, result)
                if result is not None:
                    results.append(result)
                if control is not None and control == False:
                    if self.loop:
                        idx = 0
                        continue
                    else:
                        break
                elif control is not None and control == True:
                    break
            idx += 1

            # could also persist after each operation runs - make an option?

        return results, None