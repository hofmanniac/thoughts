Examples
=====================

See the samples folder in the GitHub project (https://github.com/hofmanniac/thoughts) for examples on various rules and commands.

## read an rss feed and output it to the console at a readable rate
    [
        {"when": "rss digg.top",
        "then": [{"#read-rss": "$?feed", "into": "rss"},
                {"#output": "$rss.title", "rate": 0.0225}]
        },

        {"item": "digg", "top": "https://digg.com/rss/top.rss"}
    ]