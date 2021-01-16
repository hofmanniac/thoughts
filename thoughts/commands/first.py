from thoughts import context as ctx

def process(command, context):
    
    target = command["#first"]

    result = None
    if type(target) is list:
        result = target[0]
    elif type(target) is str:
        parts = str.split(target, " ")
        result = parts[0]

    ctx.Context.store_item(context, command, result)
    return result