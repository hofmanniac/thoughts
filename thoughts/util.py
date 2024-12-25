
def convert_to_list(item):
    if isinstance(item, list):
        result = []
        for sub_item in item:
            result.extend(convert_to_list(sub_item))
        return result
    elif isinstance(item, str):
        return item.split('\n')
    else:
        return [item]

colors = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "reset": "\033[0m"
    }

def console_log(message, color):
    color_code = colors.get(color.lower(), colors["reset"])
    print(f"{color_code}{message}{colors['reset']}")
