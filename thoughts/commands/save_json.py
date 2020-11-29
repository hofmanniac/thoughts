import thoughts.context
import json

def process(command, context):
    
    file = command["#save-json"]
    fromset = command["from"]

    if fromset in context.items:
        data = context.items[fromset]
        with open(file, 'w') as f: json.dump(data, f)