from thoughts import context as ctx
import thoughts.unification

def process(command, context: ctx.Context):

    result = []

    text = command["#tokenize"]

    tokens = text.split()

    # for positional information
    pos = 0

    for token in tokens:
        
        new_fact = {}

        if "assert" in command:        
            template = command["assert"]
            unification = {}
            unification["#"] = token
            new_fact = context.apply_values(template, unification)
        else:
            new_fact["#"] = token

        # add position information
        new_fact["#seq-start"] = pos
        new_fact["#seq-end"] = pos + 1
        pos = pos + 1
        
        result.append(new_fact)

    if (len(result) == 0): return None
    else: return result