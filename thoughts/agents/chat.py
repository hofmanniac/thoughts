from thoughts.operations.core import Operation
from thoughts.operations.console import ConsoleReader, ConsoleWriter
from thoughts.operations.memory import MessagesSummarizer
from thoughts.operations.prompting import ContextItemAppender, AppendHistory, PromptConstructor, PromptRunner, Role
from thoughts.context import Context
from thoughts.agent import PipelineExecutor

class ChatAgent(Operation):

    def __init__(self, context: Context, prompt_name: str, user_prompt: str = ":", num_chat_history: int = 4, prompt_path: str = None, init_prompt_name: str = None, init_context: Operation = None, handle_io: bool = True):
        self.context = context
        self.prompt_path = prompt_path
        self.init_prompt_name = init_prompt_name
        self.init_context: Operation = init_context
        self.prompt_name = prompt_name
        self.user_prompt = user_prompt
        self.num_chat_history = num_chat_history
        self.handle_io = handle_io

    def execute(self, context = None, message = None):

        if context is None:
            context = self.context

        reader = ConsoleReader(self.user_prompt)
        writer = ConsoleWriter()

        # start the conversation
        started = context.get_item("started", False)
        if started == False:

            if self.init_prompt_name is not None:
                chat_start = Role(self.init_prompt_name)
            else:
                chat_start = Role(self.prompt_name)

            if self.init_context:
                constructor = PromptConstructor([chat_start, self.init_context])
            else:
                constructor = PromptConstructor([chat_start])

            runner = PromptRunner(prompt_constructor=constructor)
            if self.handle_io == True:
                pipeline = PipelineExecutor([runner, writer], context)
                pipeline.execute()
                context.set_item("started", True)
            else:
                pipeline = PipelineExecutor([runner], context)
                result, control = pipeline.execute()
                context.set_item("started", True)
                result = result[0] if len(result) > 0 else None
                return result, control
                
        elif started == True and message is None:

            last_message = context.get_last_message()
            if self.handle_io == True:
                writer.execute(context, last_message)
            else:
                return last_message, None

        # main chat loop
        chat_continue = Role(self.prompt_name)
        chat_summary = ContextItemAppender(prompt_name="chat-summary", item_key="chat-summary")
        chat_history = AppendHistory(num_messages=self.num_chat_history)
        constructor = PromptConstructor([chat_continue, chat_summary, chat_history])
        runner = PromptRunner(prompt_constructor=constructor)
        summarizer = MessagesSummarizer(
            "chat-summarize", self.num_chat_history, "chat-summary", allow_partial_batch=False)

        if self.handle_io == True:
            # run the chat
            pipeline = PipelineExecutor([reader, runner, writer, summarizer], context, loop=True)
            result, control = pipeline.execute(message=message)
            return result, control
        else:
            pipeline = PipelineExecutor([runner, summarizer], context, loop=False)
            result, control = pipeline.execute(message=message)
            result = result[0] if len(result) > 0 else None
            return result, control

