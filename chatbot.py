from datetime import datetime
from thoughts.interfaces.messaging import PromptMessage
from thoughts.operations.console import ConsoleReader, ConsoleWriter
from thoughts.operations.memory import InformationExtractor, MessagesSummarizer, SessionIterator
from thoughts.operations.prompting import PromptRunner
from thoughts.engine import Context
from thoughts.engine import PipelineExecutor

def extract_followups():
    context = Context(prompt_path="extract-info")
    # info_extractor = InformationExtractor(extractor_prompt="extract-bio")
    info_extractor = InformationExtractor(extractor_prompt="extract-followups")
    iterator = SessionIterator([info_extractor])
    conclusions, control = iterator.execute(context)
    conclusion: PromptMessage
    results = []
    for conclusion in conclusions:
        # print(conclusion.content)
        results.append(conclusion)
    return "\n".join(results)

session_id = datetime.now().strftime("%Y-%m-%d")
context = Context(prompt_path="chat", session_id=session_id)

reader = ConsoleReader("YOU:")
writer = ConsoleWriter()

# start the conversation
started = context.get_item("started", False)
if started == False:
    follow_ups = context.get_item("follow-ups") or extract_followups()
    context.set_item("follow-ups", follow_ups)
    runner = PromptRunner("chat-start")
    pipeline = PipelineExecutor([runner, writer], context)
    pipeline.execute()
    context.set_item("started", True)
else:
    last_message = context.get_last_message()
    writer.execute(context, last_message)

# main chat loop
context.set_item("chat-summary", "- None")
runner = PromptRunner("chat-continue", num_chat_history=4)
summarizer = MessagesSummarizer("chat-summarize", 4, "chat-summary")

# run the game
pipeline = PipelineExecutor([reader, runner, writer, summarizer], context, loop=True)
pipeline.execute()

# extract follow ups for next time
follow_ups = extract_followups()
print(follow_ups)