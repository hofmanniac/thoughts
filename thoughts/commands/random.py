import random
from thoughts import context as ctx

def process(command, context):
    
    random_set = command["#random"]
    
    if (type(random_set) is list):
        max = len(random_set)
        r = random.randint(0, max-1)
        item = random_set[r]
        ctx.Context.store_item(context, command, item)
        return random_set[r]
