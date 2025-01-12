from thoughts import context as ctx

def process(command, context):
    
    target = command["#rest"]

    result = None
    if type(target) is list:
        result = target[1:]
    elif type(target) is str:
        parts = str.split(target, " ")
        result = parts[1:]

    ctx.RulesContext.store_item(context, command, result)
    return result