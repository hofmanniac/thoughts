import thoughts.unification

def process(command, context):

    result = []

    text = command["#tokenize"]

    tokens = text.split()

    # for positional information
    pos = 0

    for token in tokens:

        unification = {}
        unification["#"] = token
        apply = command["assert"]
        new_apply = thoughts.unification.apply_unification(apply, unification)
        
        # add position information
        new_apply["#seq-start"] = pos
        new_apply["#seq-end"] = pos + 1
        pos = pos + 1
        
        result.append(new_apply)

    if (len(result) == 0): return None
    else: return result