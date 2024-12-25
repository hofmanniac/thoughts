import json
from thoughts.context import Context
from thoughts.operations.workflow import PipelineExecutor
# import os
# import uuid
# from thoughts.interfaces.llm import LLM
# from thoughts.interfaces.memory import Memory, MemoryModule
# from thoughts.interfaces.messaging import AIMessage, HumanMessage, PromptMessage
# from thoughts.operations.agent import Agent
# from thoughts.operations.core import Operation
# from thoughts import unification
# from thoughts import util
# import json
# from thoughts.operations.prompting import PromptStarter, PromptAppender, PromptConstructor, PromptRunner
# from thoughts.operations.console import ConsoleReader, ConsoleWriter
# from thoughts.operations.memory import MemoryKeeper, TextSplitter

def create_from_json(context: Context, config_path):
    with open(config_path, 'r') as file:
        config = json.load(file)
    pipeline = PipelineExecutor.parse_json(context, config, config)
    return pipeline