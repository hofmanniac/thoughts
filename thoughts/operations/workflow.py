from thoughts.context import Context
from thoughts.operations.core import Operation
from thoughts.operations.routing import Choice
from thoughts.operations.thought import Express, Thought
from thoughts.operations.console import ConsoleReader, ConsoleWriter
from thoughts.parser import ConfigParser
# from thoughts.operations.memory import MemoryKeeper, TextSplitter

class Node:
    def __init__(self, name: str, operation: Operation, condition=None):
        self.name = name
        self.operation = operation
        self.condition = condition

    def execute(self, context, message=None):
        return self.operation.execute(context, message)  # Pass context to operation

class GraphExecutor:
    def __init__(self, context = None):
        self.nodes = {}
        self.edges = {}
        # self.context = context if context is not None else Context()

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

    def execute(self, start_node_name, context=None, message=None):

        # if context is not None:
        #     self.context = context

        if start_node_name not in self.nodes:
            raise ValueError("Start node must exist in the graph.")
        
        current_node: Node = self.nodes[start_node_name]
        while current_node:
            if not current_node.condition or current_node.condition(context):
                message, control = current_node.execute(context, message)
                # print(f"Output of {current_node.operation}: {context.data}")
            next_node = None
            for node_name, condition in self.edges.get(current_node.name, []):
                node = self.nodes[node_name]
                if condition is None or condition(context):
                    next_node = node
                    break
            current_node = next_node

class PipelineExecutor(Operation):
    """
    PipelineExecutor is a class designed to execute a sequence of nodes (operations) in a defined order.

    Parameters:
    - nodes (list): Set this parameter to the list of nodes you want to execute in sequence.
    - context (Context, optional): Provide a context object to hold shared data and state across nodes. If not provided, a new Context object is created.
    - loop (bool, optional): Set this flag to True if you want the execution to loop back to the first node after reaching the end. Defaults to False.

    Usage:
    - Initialize the PipelineExecutor with a list of nodes and optionally a context and loop flag.
    - Call the execute method with an optional context and message to start the execution process.
    - The execute method processes each node in sequence, passing the context and message through each node's execute method.
    - If the loop flag is set to True, the execution will restart from the first node after reaching the end.
    - The execution stops if a node returns a control value of False, unless the loop flag is set to True.
    """
    def __init__(self, name: str = None, nodes=[], loop = False, max_runs = None):
        self.name = name
        self.nodes = nodes
        self.loop = loop
        self.condition = None
        self.max_runs = max_runs

    def execute(self, context: Context = None, message = None):

        context.logger("PipelineExecutor: Start", "cyan")
        
        if self.nodes is None:
            return None, None
        
        result = message
        idx = 0
        results = []
        num_runs = 1
        
        while True:

            # detect if done or need to loop back to the first node
            if idx >= len(self.nodes):

                # check if max_runs is reached
                num_runs += 1
                if self.max_runs is not None and num_runs > self.max_runs:
                    break

                # # persist the context after each run
                # self.context.persist()
                # result = None
                if self.loop:
                    idx = 0
                else:
                    break
            
            # run the next operation
            current_node: Node = self.nodes[idx]
            context.logger("\t" + type(current_node).__name__, "cyan")
            # if not current_node.condition or current_node.condition(context):
            if not current_node.condition:
                result, control = current_node.execute(context, result)
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
    
    @classmethod
    def parse_json(cls, json_snippet, config):

        name = json_snippet.get("Task", None)

        # repeat = json_snippet.get("repeat", 0) if type(json_snippet) is dict else 0
        repeat = json_snippet.get("repeat", False)
        max_runs = json_snippet.get("maxRuns", None)
        if max_runs is not None and max_runs > 1:
            repeat = True

        # nodes = []

        nodes = ConfigParser.parse_operations(json_snippet["steps"], config)
        
        # for item in json_snippet["steps"]:
        #     if "MessageReader" in item or "Ask" in item:
        #         nodes.append(ConsoleReader.parse_json(item, config))
        #     elif "MessageWriter" in item or "Write" in item:
        #         nodes.append(ConsoleWriter.parse_json(item, config))
        #     elif "Thought" in item:
        #         nodes.append(Thought.parse_json(item, config))
        #     elif "Express" in item:
        #         nodes.append(Express.parse_json(item, config))
        #     elif "PipelineExecutor" in item or "Task" in item:
        #         nodes.append(PipelineExecutor.parse_json(item, config))
        #     elif "Choice" in item:
        #         nodes.append(Choice.parse_json(item, config))
        #     # if "think" in item or "PromptRunner" in item:
        #     #     nodes.append(PromptRunner.parse_json(item, config))
        #     # elif "communicate" in item:
        #     #     nodes.append(PromptRunner.parse_json(item, config))
        #     #     nodes.append(ConsoleWriter.parse_json(item, config))
        #     # elif "remember" in item:
        #     #     prompt_runner = PromptRunner.parse_json(item, config)
        #     #     prompt_runner.append_history = False # internal thought vs. communication
        #     #     nodes.append(prompt_runner)
        #     #     nodes.append(MemoryKeeper.parse_json(item, config))
        #     # elif "MemoryKeeper" in item:
        #     #     nodes.append(MemoryKeeper.parse_json(item, config))
        #     # elif "TextSplitter" in item:
        #     #     nodes.append(TextSplitter.parse_json(item, config))
        #     # elif "Analyze" in item:
        #     #     nodes.append(AnalyzeMessages.parse_json(item, config))
        #     # elif "recall" in item or "ContextMemoryAppender" in item:
        #     #     nodes.append(ContextMemoryAppender.parse_json(item, config))
        #     else:
        #         # raise ValueError(f"Unknown component in PipelineExecutor: {item}")
        #         print(f"Warning: Unknown component in PipelineExecutor: {item}")
            
        return cls(name=name, nodes=nodes, loop=repeat, max_runs=max_runs)