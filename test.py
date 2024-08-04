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
    test_data = [
        "The quick brown fox jumps over the lazy dog.",
        "A fast brown fox leaps over a sleepy canine.",
        "A speedy brown fox hops over a tired dog.",
        "A swift brown fox vaults over an exhausted dog.",
        "The quick brown fox jumped over the lazy dog.",
        "A quick brown fox jumps over the lazy dog.",
        "The quick brown fox jumps over a lazy dog.",
        "A brown fox jumps over the lazy dog quickly.",
        "In the city, the busy streets were filled with cars and people.",
        "The bustling metropolis was alive with activity.",
        "Cars honked and people hurried along the crowded sidewalks.",
        "Skyscrapers towered over the busy streets filled with honking cars.",
        "The city was a hive of activity, with people rushing everywhere.",
        "The urban landscape was a blur of motion and noise.",
        "The bustling city streets were filled with the sounds of traffic.",
        "A brown dog was walking in the park with its owner.",
        "In the park, children were playing and dogs were running around.",
        "People were enjoying a sunny day in the park with their pets.",
        "The park was filled with laughter and the sounds of dogs barking.",
        "On a sunny day, the park was crowded with people and their pets.",
        "The park was a popular spot for dog owners and families.",
        "Families and their pets enjoyed a day out in the park.",
        "The serene park was a perfect place for a walk with a dog.",
        "Children laughed and played while dogs ran in the park.",
        "The mountains stood tall and majestic against the clear blue sky.",
        "Hikers enjoyed the breathtaking views from the mountain trails.",
        "The mountain air was crisp and fresh, perfect for hiking.",
        "Snow-capped peaks glistened under the bright sun.",
        "The trail wound through the mountains, offering stunning views.",
        "In the mountains, nature was untouched and beautiful.",
        "The mountains offered a peaceful escape from the city.",
        "Hiking in the mountains was a popular activity for nature lovers.",
        "The sound of birds filled the air as hikers climbed the trails.",
        "The mountain trails provided a challenging but rewarding hike.",
        "The beach was a perfect place to relax and enjoy the ocean breeze.",
        "Waves crashed against the shore as people walked along the beach.",
        "The sun set over the ocean, casting a golden glow on the beach.",
        "People built sandcastles and played in the surf.",
        "The sandy beach stretched for miles along the coastline.",
        "Seagulls called out as they flew over the waves.",
        "The ocean waves created a soothing soundtrack at the beach.",
        "The beach was a favorite destination for families on vacation.",
        "Couples walked hand in hand along the sandy shore.",
        "The beach was alive with the sounds of laughter and crashing waves.",
        "Beachgoers enjoyed the warm sun and cool ocean water.",
        "The beach was a haven for those seeking relaxation by the sea."
    ]

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

    # List of test data
    test_data = [
        "These items are about animals",
        "These items are about nature scenes",
        "These items are about cities",
        "These items are about personal relationships",

        "The quick brown fox jumps over the lazy dog.",
        "A brown fox jumps over the lazy dog quickly.",
        "In the city, the busy streets were filled with cars and people.",
        "The bustling metropolis was alive with activity.",
        "Cars honked and people hurried along the crowded sidewalks.",
        "Skyscrapers towered over the busy streets filled with honking cars.",
        "The city was a hive of activity, with people rushing everywhere.",
        "A swift brown fox vaults over an exhausted dog.",
        "The urban landscape was a blur of motion and noise.",
        "The bustling city streets were filled with the sounds of traffic.",
        "A brown dog was walking in the park with its owner.",
        "In the park, children were playing and dogs were running around.",
        "A quick brown fox jumps over the lazy dog.",
        "People were enjoying a sunny day in the park with their pets.",
        "The park was filled with laughter and the sounds of dogs barking.",
        "On a sunny day, the park was crowded with people and their pets.",
        "The park was a popular spot for dog owners and families.",
        "Families and their pets enjoyed a day out in the park.",
        "The serene park was a perfect place for a walk with a dog.",
        "Children laughed and played while dogs ran in the park.",
        "The mountains stood tall and majestic against the clear blue sky.",
        "Hikers enjoyed the breathtaking views from the mountain trails.",
        "A speedy brown fox hops over a tired dog.",
        "The mountain air was crisp and fresh, perfect for hiking.",
        "The quick brown fox jumped over the lazy dog.",
        "Snow-capped peaks glistened under the bright sun.",
        "The trail wound through the mountains, offering stunning views.",
        "In the mountains, nature was untouched and beautiful.",
        "The mountains offered a peaceful escape from the city.",
        "Hiking in the mountains was a popular activity for nature lovers.",
        "The sound of birds filled the air as hikers climbed the trails.",
        "The mountain trails provided a challenging but rewarding hike.",
        "A fast brown fox leaps over a sleepy canine.",
        "The beach was a perfect place to relax and enjoy the ocean breeze.",
        "Waves crashed against the shore as people walked along the beach.",
        "The quick brown fox jumps over a lazy dog.",
        "The sun set over the ocean, casting a golden glow on the beach.",
        "People built sandcastles and played in the surf.",
        "The sandy beach stretched for miles along the coastline.",
        "Seagulls called out as they flew over the waves.",
        "The ocean waves created a soothing soundtrack at the beach.",
        "The beach was a favorite destination for families on vacation.",
        "Couples walked hand in hand along the sandy shore.",
        "The beach was alive with the sounds of laughter and crashing waves.",
        "Beachgoers enjoyed the warm sun and cool ocean water.",
        "The beach was a haven for those seeking relaxation by the sea."
    ]

    # test_data = [
    #     "In 1492, Christopher Columbus sailed the ocean blue and discovered the New World.",
    #     "The Great Wall of China was built over several centuries, beginning in the 7th century BC.",
    #     "The first successful airplane flight by the Wright brothers occurred on December 17, 1903.",
    #     "The Titanic, a British passenger liner, sank on its maiden voyage in April 1912.",
    #     "The Declaration of Independence was signed on July 4, 1776, marking the birth of the United States.",
    #     "The Berlin Wall, a symbol of the Cold War, fell on November 9, 1989.",
    #     "The first manned moon landing was achieved by Apollo 11 on July 20, 1969.",
    #     "The Magna Carta, signed in 1215, limited the power of the English monarchy and laid the foundation for modern democracy.",
    #     "The Renaissance, a period of cultural revival, began in Italy in the 14th century.",
    #     "The Industrial Revolution started in the late 18th century and transformed manufacturing processes.",
    #     "World War I began in 1914 and ended in 1918 with the signing of the Treaty of Versailles.",
    #     "World War II lasted from 1939 to 1945 and resulted in significant geopolitical changes.",
    #     "The French Revolution, which began in 1789, led to the rise of democracy and the fall of the monarchy in France.",
    #     "The Roman Empire, one of the largest empires in history, lasted from 27 BC to 476 AD.",
    #     "Gutenberg's invention of the printing press in 1440 revolutionized the spread of information.",
    #     "The American Civil War, fought from 1861 to 1865, was primarily over the issue of slavery.",
    #     "Alexander the Great created one of the largest empires in history by the time of his death in 323 BC.",
    #     "The signing of the Treaty of Westphalia in 1648 ended the Thirty Years' War in Europe.",
    #     "The first atomic bomb was dropped on Hiroshima, Japan, on August 6, 1945.",
    #     "Nelson Mandela was released from prison in 1990 after 27 years of imprisonment.",
    #     "The Black Death, a devastating pandemic, swept through Europe in the 14th century.",
    #     "The United Nations was founded on October 24, 1945, to promote international cooperation.",
    #     "The discovery of penicillin by Alexander Fleming in 1928 revolutionized medicine.",
    #     "The Battle of Waterloo in 1815 marked the end of Napoleon Bonaparte's rule.",
    #     "The Space Race between the United States and the Soviet Union began in the 1950s.",
    #     "The Vietnam War, a prolonged conflict, lasted from 1955 to 1975.",
    #     "The invention of the telephone by Alexander Graham Bell occurred in 1876.",
    #     "The fall of Constantinople in 1453 marked the end of the Byzantine Empire.",
    #     "The signing of the Camp David Accords in 1978 was a significant step towards peace in the Middle East.",
    #     "The Cuban Missile Crisis in 1962 brought the world to the brink of nuclear war.",
    #     "The invention of the internet in the late 20th century revolutionized communication.",
    #     "The assassination of Archduke Franz Ferdinand in 1914 triggered World War I.",
    #     "The discovery of America by Leif Erikson around the year 1000 is considered the first European visit to North America.",
    #     "The construction of the Panama Canal, completed in 1914, significantly shortened maritime travel times.",
    #     "The collapse of the Soviet Union in 1991 marked the end of the Cold War.",
    #     "The Battle of Hastings in 1066 led to the Norman conquest of England.",
    #     "The sinking of the Lusitania in 1915 influenced the United States' decision to enter World War I.",
    #     "The Suez Canal, opened in 1869, connected the Mediterranean Sea to the Red Sea.",
    #     "The Salem Witch Trials took place in colonial Massachusetts between 1692 and 1693.",
    #     "The Boston Tea Party in 1773 was a protest against British taxation policies.",
    #     "The first successful human heart transplant was performed by Dr. Christiaan Barnard in 1967.",
    #     "The construction of the Eiffel Tower was completed in 1889 for the Paris Exposition.",
    #     "The Spanish Armada was defeated by the English navy in 1588.",
    #     "The first human to journey into outer space was Yuri Gagarin in 1961.",
    #     "The discovery of the Rosetta Stone in 1799 was key to deciphering Egyptian hieroglyphs.",
    #     "The Hundred Years' War between England and France lasted from 1337 to 1453.",
    #     "The Battle of Gettysburg in 1863 was a turning point in the American Civil War.",
    #     "The abolition of slavery in the United States was achieved with the 13th Amendment in 1865."
    # ]

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
test_semantic_tree()
