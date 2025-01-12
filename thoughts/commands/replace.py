from thoughts import context as ctx
import time

def process(command, context: ctx.RulesContext):
    
    target = command["#replace"]

    if type(target) is str:

        withset = command["with"]

        if type(withset) is not dict: return target

        new_text = ""
        tokens = str.split(target, " ")
        start_pos, end_pos = 0, len(tokens)

        while (start_pos < len(tokens)):

            candidate = ""
            token_range = tokens[start_pos: end_pos]
            for token in token_range: candidate = candidate + " " + token
            candidate = candidate.strip()
            # print("trying", candidate)

            matched = False
            for key in withset.keys():
                match_key = str.strip(key)
                if match_key == candidate:
                    # print("...matched on", key)
                    new_val = withset[key]
                    new_val = str.strip(new_val)
                    new_text = new_text + " " + new_val
                    start_pos = end_pos
                    end_pos = len(tokens)
                    matched = True
                    break

            if matched == False:
                end_pos = end_pos - 1
                if end_pos == start_pos:
                    new_text = new_text + " " + candidate
                    start_pos = start_pos + 1
                    end_pos = len(tokens)
                    
        return new_text.strip() 

def process2(command, context):
    
    target = command["#replace"]
    # target = ctx.RulesContext.find_item(target)

    withset = command["with"]

    found_val = search_in_set(target, withset)
    if found_val is None: 
        found_val = search_in_set(" " + target + " ", withset)

    if found_val is not None: 
        new_val = found_val
        new_val = str.strip(new_val)
        ctx.RulesContext.store_item(context, command, new_val)
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