from datetime import datetime
from thoughts.interfaces.messaging import PromptMessage
from thoughts.operations.console import ConsoleReader, ConsoleWriter
from thoughts.operations.memory import InformationExtractor, MessagesSummarizer, SessionIterator
from thoughts.operations.prompting import ContextItemAppender, AppendHistory, IncludeContext, PromptConstructor, PromptRunner, Role
from thoughts.context import Context
from thoughts.agent import PipelineExecutor
from thoughts.operations.rules import HasValue, LogicRule, RulesRunner

# def extract_followups():
#     context = Context(prompt_path="extract-info")
#     # info_extractor = InformationExtractor(extractor_prompt="extract-bio")
#     info_extractor = InformationExtractor(extractor_prompt="extract-followups")
#     iterator = SessionIterator([info_extractor])
#     conclusions, control = iterator.execute(context)
#     conclusion: PromptMessage
#     results = []
#     for conclusion in conclusions:
#         # print(conclusion.content)
#         results.append(conclusion)
#     return "\n".join(results)

session_id = datetime.now().strftime("%Y-%m-%d")
context = Context(content_path="chat", session_id=session_id)

reader = ConsoleReader("YOU:")
writer = ConsoleWriter()

# start the conversation
started = context.get_item("started", False)
if started == False:

    chat_start = Role("chat-start")

    chat_topic = LogicRule(
        HasValue("follow-ups"), 
        [ContextItemAppender(prompt_name="chat-followups", item_key="follow-ups")], 
        [IncludeContext(prompt_name="chat-new")])

    constructor = PromptConstructor([chat_start, chat_topic])
    runner = PromptRunner(prompt_constructor=constructor)
    pipeline = PipelineExecutor([runner, writer], context)

    init_result, control = pipeline.execute()
    context.set_item("started", True)
else:
    last_message = context.get_last_message()
    writer.execute(context, last_message)

# main chat loop
chat_continue = Role("chat-continue")
chat_summary = ContextItemAppender(prompt_name="chat-summary", item_key="chat-summary")
chat_history = AppendHistory(num_messages=4)
constructor = PromptConstructor([chat_continue, chat_summary, chat_history])
runner = PromptRunner(prompt_constructor=constructor)
summarizer = MessagesSummarizer("chat-summarize", 4, "chat-summary")

# run the game
pipeline = PipelineExecutor([reader, runner, writer, summarizer], context, loop=True)
pipeline.execute()

# extract follow ups for next time
# follow_ups = extract_followups()
# print(follow_ups)