from thoughts.interfaces.messaging import HumanMessage


def test_llm():

    from thoughts.interfaces.llm import LLM
    from thoughts.interfaces.messaging import HumanMessage

    llm = LLM()
    messages = [HumanMessage(content="How big is the United States?")]
    response = llm.invoke(messages)
    print(response.content)


def test_graph_executor():

    from thoughts.engine import GraphExecutor
    from thoughts.operations.prompting import PromptRunner
    from thoughts.operations.console import ConsoleReader, ConsoleWriter

    graph = GraphExecutor()
    graph.add_node("reader", ConsoleReader(":"))
    graph.add_node(
        "responder", PromptRunner(prompt_name="assistant", num_chat_history=4)
    )
    graph.add_node("writer", ConsoleWriter())
    graph.add_edge("reader", "responder")
    graph.add_edge("responder", "writer")
    graph.add_edge("writer", "reader")
    graph.execute(start_node_name="responder")


def test_prompt_constructor():
    from thoughts.operations.prompting import StaticPromptLoader
    from thoughts.engine import Context

    context = Context()
    static_loader = StaticPromptLoader("assistant")
    static_loader.execute(context)

    prompt = context.get("prompt")
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

    context.push(HumanMessage(content="Who wrote 'Great Expectations'?"))
    ai_message = prompt_runner.execute(context)
    print(ai_message)

    context.push(HumanMessage(content="What kind of dog do I have?"))
    ai_message = prompt_runner.execute(context)
    print(ai_message)

# test_llm()
# test_graph_executor()
# test_prompt_constructor()

# test_memory()

# test_prompt_runner_simple()
test_prompt_runner_complex()

