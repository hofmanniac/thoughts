from thoughts import context as ctx
# import re

def process(command, context):
    
    target = command["#replace"]
    withset = command["with"]

    tokens = str.split(target)

    new_val = ""

    for token in tokens:
        if token in withset:
            new_val = new_val + withset[token]
        else:
            new_val = token
        new_val = new_val + " "
    
    new_val = str.strip(new_val)

    return new_val
