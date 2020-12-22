import thoughts.unification
import copy

def process(command, context):

    result = []

    target = command["#lookup"]

    # search through all items in the context
    for item in context.rules:

        # test if this item matches
        unification = thoughts.unification.unify(item, target)
        
        # if the item matches
        if (unification is not None):

            new_item = copy.deepcopy(item)

            # add position information (inherited from lookup command)    
            if (type(new_item) is dict): 
                if ("#seq-start" in command): new_item["#seq-start"] = command["#seq-start"]
                if ("#seq-end" in command): new_item["#seq-end"] = command["#seq-end"]

            # add found item to results
            result.append(new_item)

    # if not result, then echo back the value as-is
    if (len(result) == 0):
        new_item = copy.deepcopy(target)
        # add position information (inherited from lookup command)    
        if (type(new_item) is dict): 
            if ("#seq-start" in command): new_item["#seq-start"] = command["#seq-start"]
            if ("#seq-end" in command): new_item["#seq-end"] = command["#seq-end"]
        result.append(new_item)

    # return all results
    return result
