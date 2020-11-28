thoughts framework
====================

thoughts is a lightweight rules-based engine

How To Use:
====================

# add a .json file that contains your rules:
[
    {   "when": "hello",
        "then": {"#output": "hello, world!"}
    }
]

# import the engine
from thoughts.rules_engine import RulesEngine

# start a new engine and load the rule file above
engine = RulesEngine()
engine.load_rules("rules.json")

# alternatively, you can create a manual rule without loading a file
rule = {"when": "what time is it", "then": {"#output": "time to get a new watch"}}
engine.add_rule(rule)

# define and run assertions
assertion = "hello"
engine.run_assert(assertion)

# assertions will match the "when" portion of rules, based on a unification algorithm:
* Strings will match direct string matches, "when": "hello" will match "hello"
* Strings will match using variables, "when": "my dog is ?name" will match "my dog is fido"
* Dictionaries will match a dictionary, "when": {"name": "fido"} will match {"name": "fido"}

# if the assertion matches, the "then" portion will fire
# rules will "forward chain" - the "then" portion of rules will cause the engine to match against rules
[
    {   "when": "hello",
        "then": {"user-intent": "greet"}
    },

    {   "when": {"user-intent": "greet"},
        "then": {"#output": "hello, world"}
    }
]

# you can have more than one command (action) in the "then" portion
{   "when": "hello",
    "then": [{"#output": "hello there"}, 
             {"#output": "nice to meet you"}]
}

# you can store "item" knowledge (facts)
{"item": "user", "name": "jeremy", "dog": "fido"}

# you can reference the items (facts) and their properties in your rules,
# using $itemname.property syntax
{"when": "what is my name",
 "then": [{"#output": "your name is $user.name"}
}

Commands
===================

You can use commands in the "then" portion of your rules. The engine will run the commands if the "when" portion matches.

In this version, only three commands are available

# #output
* Behavior: Will echo the text to the console (using print)
* Example: {"#output": "hello, world"}
* Optional: specifiy a "rate" to slow output the contents to the console

# #prompt
* Behavior: Will ask for input and store into an item
* Example: {"#input": "what is your name", "into": "username"}

# #read-rss
* Behavior: Will read the specified rss feed into an item
* Example: {"#read-rss": "https://rss-feed.rss", "into": "rss"}


Examples
=====================

# read an rss feed and output it to the console at a readable rate
[
    {"when": "rss digg.top",
     "then": [{"#read-rss": "$?feed", "into": "rss"},
              {"#output": "$rss.title", "rate": 0.0225}]
    },

    {"item": "digg", "top": "https://digg.com/rss/top.rss"}
]