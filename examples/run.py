import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime
from thoughts.context import Context
from thoughts.agent import Agent

def run_example(example):
    agent = Agent()

    if example["name"] == "Chatbot":
        session_id = datetime.now().strftime("%Y-%m-%d")
        context = Context(session_id=session_id)
    elif example["name"] == "Steampunk Game":
        context = Context(content_path="games", persist_session=False)
    else:
        context = Context(persist_session=False)

    agent.load_from_config(context, example["path"])
    agent.execute(context)


examples = [
    
    {"name": "Pirate Chatbot", "path": "examples/chatbots/pirate-bot.json"},
    {"name": "Chatbot", "path": "examples/chatbots/chatbot.json"},

    {"name": "Dungeon Game", "path": "examples/games/dungeon.json"},
    {"name": "Spaceship Game", "path": "examples/games/spaceship.json"},
    {"name": "Steampunk Game", "path": "examples/games/game.json"},

    {"name": "Comedians", "path": "examples/workflow/comedians.json"},
    {"name": "Data Modeling", "path": "examples/workflow/data-modeling.json"},
    {"name": "Politics", "path": "examples/workflow/politics.json"},
    {"name": "Story Ideas", "path": "examples/workflow/story-ideas.json"}
]

choice = input("Choose an example to run:\n" + "\n".join([f"{i+1}. {e['name']}" for i, e in enumerate(examples)]) + "\n\n: ")
example = examples[int(choice)-1]
run_example(example)