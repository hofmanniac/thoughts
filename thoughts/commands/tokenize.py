from thoughts import context as ctx
import thoughts.unification

def process(command, context: ctx.RulesContext):

    result = []

    text = command["#tokenize"]

    if type(text) is str:
        tokens = text.split()
    elif type(text) is list:
        tokens = text

    # for positional information
    pos = 0

    for token in tokens:
        
        new_fact = {}

        if type(token) is str:
            new_fact = context.apply_values(command["assert"], {"#": token}) if "assert" in command else token
        else:
            new_fact = token
            
        if type(new_fact) is not dict and type(new_fact) is not list:
            new_fact = {"#assert": new_fact}

        # add position information
        new_fact["#seq-start"] = pos
        new_fact["#seq-end"] = pos + 1
        pos = pos + 1

        # if type(new_fact) is str:
        #     new_fact["#"] = new_fact
        #     # add position information
        #     new_fact["#seq-start"] = pos
        #     new_fact["#seq-end"] = pos + 1
        #     pos = pos + 1
        #     new_fact = {"#assert": new_fact}

        result.append(new_fact)

    if (len(result) == 0): return None
    else: return result