import thoughts.unification

def process(command, context):

    result = []

    target = command["#lookup"]

    for item in context.rules:
        unification = thoughts.unification.unify(item, target)
        if (unification is not None): result.append(item)

    return result
