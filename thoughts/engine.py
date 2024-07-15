from thoughts.interfaces.llm import LLM
from thoughts.interfaces.memory import Memory
from thoughts.operations.core import Operation

class Context:

    def __init__(self, llm: LLM = None, memory: Memory = None):
        self.data = {}
        self.llm = llm if llm is not None else LLM()
        self.memory = memory if memory is not None else Memory()
        self.messages = []

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value

    def update(self, key, value):
        if key in self.data and isinstance(self.data[key], dict) and isinstance(value, dict):
            self.data[key].update(value)
        else:
            self.data[key] = value

    def push(self, value):
        self.messages.append(value)

    def pop(self):
        self.messages.pop()

    def peek(self, num: int = 1):
        if len(self.messages) == 0:
            return []
        return self.messages[-num:] if num <= len(self.messages) else self.messages
    
    def get_last_message(self):
        return self.messages[-1] if self.messages else None



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
        self.loop = ProcessLookupError

    def execute(self, context=None):

        if context is not None:
            self.context = context
        
        idx = 0
        while True:
            if idx > len(self.nodes):
                if self.loop:
                    idx = 0
                else:
                    break
            current_node: Node = self.nodes[idx]
            if not current_node.condition or current_node.condition(self.context):
                current_node.execute(self.context)
            idx += 1
