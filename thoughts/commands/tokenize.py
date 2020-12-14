import thoughts.unification

def process(command, context):

    result = []

    text = command["#tokenize"]

    tokens = text.split()

    for token in tokens:
        unification = {}
        unification["#"] = token
        apply = command["assert"]
        new_apply = thoughts.unification.apply_unification(apply, unification)
        result.append(new_apply)

    if (len(result) == 0): return None
    else: return result