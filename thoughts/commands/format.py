from thoughts import context as ctx

def process(command, context):
    
    target = command["#format"]
    as_format = command["#as"]

    # upper, chartokens, proper, sentence

    result = None

    if as_format == "lower":
        if type(target) is str: result = str.lower(target)
    elif as_format == "upper":
        if type(target) is str: result = str.upper(target)
    elif as_format == "chartokens":
        if type(target) is str:
            if result is None: result = ""
            for char in target: result = result + char + " "
            result = str.rstrip(result)
    elif as_format == "proper":
        if type(target) is str: result = str.title(target)
    elif as_format == "sentence":
        if type(target) is str: result = str.capitalize(target)

    ctx.Context.store_item(context, command, result)
    return result
