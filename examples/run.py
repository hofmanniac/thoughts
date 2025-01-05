from datetime import datetime
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from thoughts.context import Context
from thoughts.agent import Agent

context = Context(content_path="game")

agent = Agent()

# agent.load_from_config(context, "examples/agents/comedians.json")
# agent.execute(context, "Perform Act")

# agent.load_from_config(context, "examples/game/game.json")
# agent.load_from_config(context, "examples/agents/data-modeling-2.json")
# agent.load_from_config(context, "examples/agents/politics.json")
# agent.load_from_config(context, "examples/agents/story-ideas.json")

# agent.load_from_config(context, "examples/games/dungeon.json")
agent.load_from_config(context, "examples/games/spaceship.json")

# pirate chatbot (simple)
# agent.load_from_config(context, "examples/chatbots/pirate-bot.json")

# chatbot (more complex)
# session_id = datetime.now().strftime("%Y-%m-%d")
# # context = Context(content_path="chat", session_id=session_id)
# context = Context(session_id=session_id)
# agent.load_from_config(context, "examples/chatbots/chatbot-3.json")

agent.execute(context)