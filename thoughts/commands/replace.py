from thoughts import context as ctx

def process(command, context):
    
    target = command["#replace"]
    withset = command["with"]

    new_val = " " + target + " "

    for key in withset:
        if key == "#unification": continue
        if key == "#item": continue
        
        compare_token = " " + key + " "
        new_val = str.replace(new_val, compare_token, " " + withset[key] + " " )

    return new_val