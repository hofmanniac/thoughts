import random

def process(command, context):
    
    random_set = command["#random"]
    
    if (type(random_set) is list):
        max = len(random_set)
        r = random.randint(0, max-1)
        return random_set[r]
