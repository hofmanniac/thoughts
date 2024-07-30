from thoughts.engine import Context
from thoughts.operations.core import Operation

from thoughts.engine import PipelineExecutor
from thoughts.operations.prompting import PromptRunner
from thoughts.operations.console import ConsoleReader, ConsoleWriter

class ChatAgent(Operation):
    def __init__(self, prompt_name: str, user_prompt: str = ":", num_chat_history: int = 4):
        self.prompt_name = prompt_name
        self.user_prompt = user_prompt
        self.num_chat_history = num_chat_history

    def execute(self, context: Context):
        pipeline = PipelineExecutor([
            PromptRunner(prompt_name=self.prompt_name, num_chat_history=self.num_chat_history), 
            ConsoleWriter(),
            ConsoleReader(self.user_prompt)
        ], loop = True)

        pipeline.execute(context)
    