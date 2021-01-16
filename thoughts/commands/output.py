import thoughts.context
import time

def process(command, context):
    
    text = command["#output"]
    item = text

    rate = 0
    if "rate" in command: rate = command["rate"]

    if (type(text) is str):
        item = thoughts.context.Context.retrieve(context, text)

    if (type(item) is str):
        slow_output(item, rate)

    elif (type(item) is dict):
        print(str(item))

    elif (type(item) is list):
        i = 1
        for it in item:
            item_to_print = "[{}] {}".format(i, str(it))
            slow_output(item_to_print, rate)
            # speed_read(item_to_print, rate)
            i = i + 1

    else:
        print(str(item))

    if "pause" in command: 
        pause = command["pause"]
        time.sleep(pause)

def speed_read(text, rate):
    
    if rate == 0: 
        print(text)

    else:
        for token in text.split(' '):
            token = token + "                    "
            print(token, end="\r")
            time.sleep(rate)

def slow_output(text, rate):

    if rate == 0: 
        print(text)

    else:
        for c in text:
            print(c, end="")
            time.sleep(rate)
        print()