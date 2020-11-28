
def process(command, context):
    
    text = command["#prompt"]
    inp = input(text + " ")

    if "into" in command:
        into = command["into"]
        context.items[into] = inp