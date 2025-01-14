import feedparser
from thoughts.context import Context
from thoughts.operations.core import Operation

# def process(command, context: thoughts.context.RulesContext):
    
#     url = command["#read-rss"]
#     items = feedparser.parse(url)

#     if "into" in command:
#         into = command["into"]
#         context.items[into] = items.entries
#     else:
#         for item in items.entries:
#             print("* ", item.title)

class FetchFeed(Operation):
    def __init__(self, url: str, into: str = None):
        self.url = url
        self.into = into
    def execute(self, context: Context, message = None):
        items = feedparser.parse(self.url)
        if self.into is not None:
            context.set_item(self.into, items.entries)
        return items.entries, None
    @classmethod
    def parse_json(cls, json_snippet, config):
        moniker = "FetchFeed"
        url = json_snippet[moniker]
        into = json_snippet.get("into", None)
        return cls(url=url, into=into)