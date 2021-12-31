from thoughts import context as ctx
import thoughts.unification
import copy

def process(command, context: ctx.Context ):

    result = []

    target = command["#lookup"]

    # first try the context items
    for key in context.items.keys():
        
        item = context.items[key]
        unification = thoughts.unification.unify(item, target)

         # if the item matches
        if (unification is not None):

            # new_item = key
            # result.append(new_item)

            new_item = copy.deepcopy(item)
            new_item["item"] = key

            # add position information (inherited from lookup command)    
            if (type(new_item) is dict): 
                if ("#seq-start" in command): new_item["#seq-start"] = command["#seq-start"]
                if ("#seq-end" in command): new_item["#seq-end"] = command["#seq-end"]

            # add found item to results
            result.append(new_item)

    if (len(result) == 0):

        # search through all items in the context
        for ruleset in context.rulesets:
            
            rules = ruleset["rules"]

            for item in rules:

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

    # if no result, then echo back the value as-is
    # dec-28 2021 - removing this for now
    # if (len(result) == 0):
    #     new_item = copy.deepcopy(target)
    #     # add position information (inherited from lookup command)    
    #     if (type(new_item) is dict): 
    #         if ("#seq-start" in command): new_item["#seq-start"] = command["#seq-start"]
    #         if ("#seq-end" in command): new_item["#seq-end"] = command["#seq-end"]
    #     result.append(new_item)

    if "#into" in command:
        context.store_item(command, result)
    else:  
        # return all results
        return result
