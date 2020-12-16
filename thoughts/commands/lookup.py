import thoughts.unification

def process(command, context):

    result = []

    target = command["#lookup"]

    # search through all items in the context
    for item in context.rules:

        # test if this item matches
        unification = thoughts.unification.unify(item, target)
        
        # if the item matches
        if (unification is not None):

            # add position information (inherited from lookup command)    
            if (type(item) is dict): 
                if ("#seq-start" in command): item["#seq-start"] = command["#seq-start"]
                if ("#seq-end" in command): item["#seq-end"] = command["#seq-end"]

            # add found item to results
            result.append(item)

    # return all results
    return result
