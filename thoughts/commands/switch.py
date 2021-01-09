from thoughts import context as ctx

def process(command, context):
    
    switch_val = command["#switch"]
    if str.startswith(switch_val, "?"): switch_val = "#unknown"
    elif str.startswith(switch_val, "$"): switch_val = "#unknown"

    options = command["#on"]

    found_option = None
    for option in options:
        
        option_val = option["#val"]

        if found_option is None and option_val == "#default": found_option = option

        if switch_val == option_val:
            found_option = option
            break
    
    if found_option is not None:
        do_part = found_option["#do"]
        return do_part
