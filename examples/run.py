import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from thoughts.engine import Context, PipelineExecutor

def create_from_json(context: Context, config_path):
    with open(config_path, 'r') as file:
        config = json.load(file)

    items = config.get("Items", [])
    # Set each item in the context using the first property as the item name and value
    for item in items:
        if isinstance(item, dict):
            for key, value in item.items():
                context.set_item(key, value)
                break  # Only use the first property

    pipeline = PipelineExecutor.parse_json(context, config, config)
    return pipeline

# create a new context - a container for all the data associated with the current state of the game
context = Context(content_path="game")

# pipeline = create_from_json(context, "examples/game/game.json")
# pipeline = create_from_json(context, "examples/agents/story-ideas.json")
pipeline = create_from_json(context, "examples/agents/comedians.json")

pipeline.execute(context)