import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from thoughts.context import Context
from thoughts.agent import Agent

context = Context(content_path="game")

agent = Agent()

# agent.load_from_config(context, "examples/agents/comedians.json")
# agent.execute(context, "Perform Act")

# agent.load_from_config(context, "examples/game/game.json")
agent.load_from_config(context, "examples/agents/data-modeling-2.json")
agent.execute(context)