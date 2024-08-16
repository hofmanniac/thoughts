from datetime import datetime
import json
import pprint
from thoughts.interfaces.messaging import HumanMessage
from thoughts.operations.console import ConsoleWriter
from thoughts.operations.prompting import ContextItemAppender, PromptRunner, PromptStarter

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

def test_convert_to_list():
    from thoughts.util import convert_to_list
    from thoughts.engine import Context
    from pprint import pprint

    context = Context(session_id="2024-07-24")
    item = context.get_item("extract-topics-12")
    result = convert_to_list(item["content"])

    pprint(result, width=120)

def test_normalize_list():
    from thoughts.util import convert_to_list
    from thoughts.engine import Context
    from pprint import pprint

    context = Context(session_id="2024-07-24", prompt_path="extract-info")
    item = context.get_item("extract-topics-12")
    items = convert_to_list(item["content"])
    items = sorted(items)

    data_prompt = "normalize-list"
    items = list(set(items))
    store_as = "normalized-list"

    messages, control = PromptStarter(content="You are a helpful AI assistant").execute(context)
    messages, control = PromptStarter(role="human", prompt_name=data_prompt).execute(context, messages)
    messages, control = ContextItemAppender(items=items).execute(context, messages)
    ai_message, control = PromptRunner(stream=False).execute(context, messages)
    # context.set_item("normalized-list", {"content": ai_message.content})
    ai_message.content = convert_to_list(ai_message.content)
    context.set_item(store_as, ai_message)

def test_semantic_memory():
    from thoughts.engine import Context
    from thoughts.operations.prompting import ContextItemAppender, PromptRunner, PromptStarter
    from thoughts.interfaces.semantic import Thought

    context = Context(session_id="semantic-memory")

    # Example usage
    memory_db = Thought(context=context, similarity_threshold=1.0)

    # Clear all memories for a clean start
    memory_db.reset()

    # # Add new memories
    # memory_db.add_memory(HumanMessage('The quick brown fox jumps over the lazy dog.'), metadata={'source': 'Example'})
    # memory_db.add_memory(HumanMessage('A fast brown fox leaps over a sleepy canine.'), metadata={'source': 'Example'})
    # memory_db.add_memory(HumanMessage('A ferret bounced over a furry wolf.'), metadata={'source': 'Example'})
    # memory_db.add_memory(HumanMessage('My very excellent mother just served us nine pizzas.'), metadata={'source': 'Example'})
    # memory_db.add_memory(HumanMessage('A swift brown fox vaults over an exhausted dog.'), metadata={'source': 'Example'})

    # List of test data
    # data_file = "samples/data/generic-sentences.json"
    data_file = "samples/data/historical-facts.json"
    with open(data_file, "r") as f:
        test_data = json.load(f)

    # Add new memories
    for sentence in test_data:
        message = HumanMessage(sentence)
        memory_db.add_memory(message)
        
    memory_db.print_clusters()

    # # Retrieve and print a memory
    # try:
    #     prompt_message, metadata = memory_db.get_memory(message.message_id)
    #     print(f"Retrieved memory: {prompt_message.content}, Embedding: {prompt_message.embedding}, Metadata: {metadata}")
    # except ValueError as e:
    #     print(e)

def test_semantic_tree():
    from thoughts.engine import Context
    from thoughts.interfaces.semantic import SemanticMemoryTree
    from thoughts.interfaces.semantic import Thought

    # data_file = "samples/data/generic-sentences.json"
    data_file = "samples/data/historical-facts.json"
    with open(data_file, "r") as f:
        test_data = json.load(f)

    # Example Usage
    context = Context(session_id="semantic-memory")
    memory_system = SemanticMemoryTree(
        context, penalty_coefficient=0.05, max_cluster_size=4, similarity_threshold=0.9)
    memory_system.reset()

    idx = 1
    # Add new memories
    for sentence in test_data:
        message = Thought(sentence, id=str(idx))
        memory_system.add_memory(message)
        idx += 1

    result = memory_system.get_memory_summary()
    session_id = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    with open("memory/semantic-tree-" + session_id + ".json", "w") as f:
        json.dump(result, f)

    # Simulate app restart and load tree from ChromaDB
    # memory_system.load_tree()
    # print(memory_system.get_memory_summary())
    
def test_semantic_clusters():
    from thoughts.engine import Context
    from thoughts.interfaces.semantic import SemanticClusters

    context = Context(session_id="semantic-clusters", persist_session=False)
    cluster_memory = SemanticClusters(context=context, hierarchical=False)

    cluster_memory.load_clusters("samples/data/history-topics.json")
    cluster_memory.load_memories("samples/data/history-items.json")

    # cluster_memory.load_clusters("samples/data/general-topics.json")
    # cluster_memory.load_memories("samples/data/general-items.json")

    # cluster_memory.load_clusters("samples/data/personal-topics.json")
    # cluster_memory.load_memories("samples/data/personal-items.json")

    datetime_stamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    path = "memory/outputs/semantic-clusters/semantic-clusters-" + datetime_stamp + "-before.json"
    cluster_memory.save_as_json(path)

    cluster_memory.consolidate_root()
    path = "memory/outputs/semantic-clusters/semantic-clusters-" + datetime_stamp + "-after.json"
    cluster_memory.save_as_json(path)

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
# test_session_iterator()
# test_convert_to_list()
# test_normalize_list()
# test_semantic_memory()
# test_semantic_tree()
test_semantic_clusters()
# test_semantic_clusters_personal()
