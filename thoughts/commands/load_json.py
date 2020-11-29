import thoughts.context
import json

def process(command, context):
    
    file = command["#load-json"]
    into = command["into"]

    with open(file) as f:
        data = json.load(f)
        context.items[into] = data

