from thoughts.interfaces.messaging import HumanMessage
from thoughts.operations.console import ConsoleWriter

def test_llm():

    from thoughts.interfaces.llm import LLM
    from thoughts.interfaces.messaging import HumanMessage

    llm = LLM()
    messages = [HumanMessage(content="How big is the United States?")]
    response = llm.invoke(messages, stream=True)
    # print(response.content)


def test_graph_executor():

    from thoughts.engine import GraphExecutor
    from thoughts.operations.prompting import PromptRunner
    from thoughts.operations.console import ConsoleReader, ConsoleWriter

    graph = GraphExecutor()
    graph.add_node("reader", ConsoleReader(":"))
    graph.add_node(
        "responder", PromptRunner(prompt_name="prompts/assistant", num_chat_history=4)
    )
    graph.add_node("writer", ConsoleWriter())
    graph.add_edge("reader", "responder")
    graph.add_edge("responder", "writer")
    graph.add_edge("writer", "reader")
    graph.execute(start_node_name="responder")

def test_pipeline_executor():
    from thoughts.engine import PipelineExecutor
    from thoughts.operations.prompting import PromptRunner
    from thoughts.operations.console import ConsoleReader, ConsoleWriter

    pipeline = PipelineExecutor([
        PromptRunner(prompt_name="assistant", num_chat_history=4), 
        ConsoleWriter(),
        ConsoleReader(":")
    ], loop = True)

    pipeline.execute()

def test_prompt_constructor():
    from thoughts.operations.prompting import StaticPromptLoader
    from thoughts.engine import Context

    context = Context()
    static_loader = StaticPromptLoader("assistant")
    static_loader.execute(context)

    prompt = context.get_item("prompt")
    print(prompt)

def test_memory():
    from thoughts.interfaces.memory import Memory

    memory = Memory()
    memory.erase_collection("temp")

    memory.add(HumanMessage(content="My dog is a Havanese."), "temp")
    memory.add(HumanMessage(content="My friend's dog is a Schnauzer."), "temp")
    memory.add(HumanMessage(content="Mars is the fourth planet in the solar system."), "temp")

    search_message = HumanMessage(content="Who wrote 'Great Expectations'?")
    memories = memory.find("temp", search_message)
    print(memories)

    search_message = HumanMessage(content="What kind of dog do I have?")
    memories = memory.find("temp", search_message)
    print(memories)

    search_message = HumanMessage(content="Saturn is the planet with rings")
    memories = memory.find("temp", search_message)
    print(memories)

def test_prompt_runner_simple():
    from thoughts.operations.prompting import PromptRunner
    from thoughts.engine import Context

    context = Context()
    prompt_runner = PromptRunner("assistant")
    ai_message = prompt_runner.execute(context)
    print(ai_message)


def test_prompt_runner_complex():
    from thoughts.operations.prompting import PromptRunner, PromptConstructor, StaticPromptLoader
    from thoughts.engine import Context
    from thoughts.operations.memory import RAGContextAdder

    context = Context()
    context.memory.erase_collection("temp")
    context.memory.add(HumanMessage(content="My dog is a Havanese."), "temp")

    prompt_runner = PromptRunner(
        prompt_constructor=PromptConstructor([
            StaticPromptLoader("assistant"), 
            RAGContextAdder("temp")])
    )

    context.push_message(HumanMessage(content="Who wrote 'Great Expectations'?"))
    ai_message = prompt_runner.execute(context)
    print(ai_message.content)

    context.clear_messages()
    context.push_message(HumanMessage(content="What kind of dog do I have?"))
    ai_message = prompt_runner.execute(context)
    print(ai_message.content)

def test_chat_agent():
    from thoughts.agents.chat import ChatAgent
    from thoughts.engine import Context

    context = Context(prompt_path="prompts", session_id="test-chat")
    chat_agent = ChatAgent(context=context, prompt_name="pirate", user_prompt="YOU:", num_chat_history=4)
    chat_agent.execute(context)
    
def test_chat_agent_loop():
    from thoughts.agents.chat import ChatAgent
    from thoughts.engine import Context
    from thoughts.operations.console import ConsoleReader

    context = Context(prompt_path="prompts", session_id="test-chat-loop")
    chat_agent = ChatAgent(
        context=context, prompt_name="pirate", user_prompt="YOU:", num_chat_history=4, handle_io=False)
    reader = ConsoleReader("YOU:")
    writer = ConsoleWriter()
    
    # bot initiates the chat
    ai_message, control = chat_agent.execute(context)
    writer.execute(context, ai_message)

    # now loop!
    while True:
        message, control = reader.execute(context)
        ai_message, control = chat_agent.execute(context, message)
        writer.execute(context, ai_message)

def test_logic_rules():
    from thoughts.operations.rules import RulesRunner
    from thoughts.operations.rules import LogicRule, Unifies
    from thoughts.operations.console import ConsoleWriter
    from thoughts.operations.rules import FactAsserter
    from thoughts.engine import Context

    rules_runner = RulesRunner()

    condition = Unifies({"game-event": "start"})
    actions = [
        ConsoleWriter(text="You are standing in a scary woods at night."),
        ConsoleWriter(text="There are even scarier sounds coming from the north."),
        ConsoleWriter(text="To go north, turn to page 15."),
        ConsoleWriter(text="To stand there and whimper like a 3-year old, turn to page 10.")]
    rule = LogicRule(condition, actions)
    rules_runner.add_rule(rule)

    condition = Unifies({"input": "15"})
    actions = [
        ConsoleWriter(text="North?? OK...."),
        ConsoleWriter(text="You go north (a terrible choice, btw) and run into goblins."),
        ConsoleWriter(text="To try talking with the goblins, turn to page 32."),
        ConsoleWriter(text="To try sneaking past the goblins, turn to page 50.")]
    rule = LogicRule(condition, actions)
    rules_runner.add_rule(rule)

    condition = Unifies({"input": "Talk with ?person"})
    actions = [
        FactAsserter({"action": "talk", "subject": "?person"})
    ]
    rule = LogicRule(condition, actions)
    rules_runner.add_rule(rule)

    condition = Unifies({"action": "talk", "subject": "?person"})
    actions = [
        ConsoleWriter(text="You try talking with ?person. They do not seem amused.")
    ]
    rule = LogicRule(condition, actions)
    rules_runner.add_rule(rule)

    context = Context()
    rules_runner.execute(context, message={"game-event": "start"})

    while True:
        print("")
        text = input(": ")
        rules_runner.execute(context, message={"input": text})

def test_message_summarizer():
    from thoughts.engine import Context
    from thoughts.operations.memory import MessagesSummarizer

    context = Context(prompt_path="chat", session_id="2024-07-26")
    summarizer = MessagesSummarizer("chat-summarize", 6, "chat-summary-6")
    results = summarizer.execute(context)

    print(results)

def test_session_iterator():
    from thoughts.engine import Context
    from thoughts.operations.memory import SessionIterator
    from thoughts.operations.memory import MessagesSummarizer

    # context = Context(prompt_path="chat")
    # summarizer = MessagesSummarizer("chat-summarize", 6, "chat-summary")

    context = Context(prompt_path="extract-info")
    # summarizer = MessagesSummarizer("extract-followups", 12, "extract-followups-12")
    summarizer = MessagesSummarizer("extract-topics", 12, "extract-topics-12")
    session_iter = SessionIterator([summarizer])
    session_iter.execute(context)

# test_llm()
# test_graph_executor()
# test_pipeline_executor()
# test_prompt_constructor()
# test_memory()
# test_prompt_runner_simple()
# test_prompt_runner_complex()
# test_chat_agent()
# test_chat_agent_loop()

# test_logic_rules()
# test_message_summarizer()
test_session_iterator()

