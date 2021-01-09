from thoughts import context as ctx
# import re

def process(command, context):
    
    target = command["#replace"]
    # target = ctx.Context.find_item(target)

    withset = command["with"]

    target = " " + target + " "
    if target in withset: target = withset[target]
    new_val = target

    # result = ""
    # temp = ""
    # for char in target:
    #     temp = temp + char
        
    # replacements = {}
    # target = " " + target + " "
    # for key in withset.keys():
    #     idx = str.rfind(target, key)
    #     if idx > -1: replacements[key] = withset[key]

    # for key in replacements.keys():
    #     new = replacements[key]
    #     target = str.replace(target, key, new)
    # new_val = target

    # tokens = str.split(target)
    # new_val = ""
    # for token in tokens:
    #     if token in withset:
    #         new_val = new_val + withset[token]
    #     else:
    #         new_val = token
    #     new_val = new_val + " "
    
    new_val = str.strip(new_val)

    ctx.Context.store_item(context, command, new_val)
    return new_val
