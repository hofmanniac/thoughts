import feedparser

def process(command, context):
    
    url = command["#read-rss"]
    items = feedparser.parse(url)

    if "into" in command:
        into = command["into"]
        context.items[into] = items.entries
    else:
        for item in items.entries:
            print("* ", item.title)