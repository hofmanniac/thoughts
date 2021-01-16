from thoughts import context as ctx
# import re

def process(command, context):
    
    target = command["#replace"]
    # target = ctx.Context.find_item(target)

    withset = command["with"]

    found_val = search_in_set(target, withset)
    if found_val is None: 
        found_val = search_in_set(" " + target + " ", withset)

    if found_val is not None: 
        new_val = found_val
        new_val = str.strip(new_val)
        ctx.Context.store_item(context, command, new_val)
        return new_val

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

def search_in_set(key, set):
    try_val = key
    found_val = None
    if try_val in set: 
        found_val = set[try_val]
    else:
        try_val = str.upper(key)
        if try_val in set:
            found_val = set[try_val]
        else:
            try_val = str.lower(key)
            if try_val in set:
                found_val = set[try_val]
    return found_val