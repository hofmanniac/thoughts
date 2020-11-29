Thoughts Rules Engine
====================

Thoughts is a lightweight rules engine.

What's New
===================

# Sun Nov-29, 2020 Release
In this release, you can now load and save .json files into Context Items. See #load-json and #save-json in the Commands section below for more information.

# Sat Nov-28, 2020 Release
In this release, you can now load custom plugins for use in the "then" portion of rules. See "load_plugin" in the Engine Methods section below for more information.

How To Use
====================

## Add a .json file that contains your rules:
    [
        {   "when": "hello",
            "then": {"#output": "hello, world!"}
        }
    ]  

See the samples folder in the GitHub project (https://github.com/hofmanniac/thoughts) for examples on various rules and commands.

## Import the engine
    from thoughts.rules_engine import RulesEngine

## Start a new engine and load the rule file above
    engine = RulesEngine()
    engine.load_rules("rules.json")

## Alternatively, you can create a manual rule without loading a file
    rule = {"when": "what time is it", "then": {"#output": "time to get a new watch"}}
    engine.add_rule(rule)

## Define and run assertions
    assertion = "hello"
    engine.run_assert(assertion)

## Assertions will match the "when" portion of rules, based on a unification algorithm:
* Strings will match direct string matches, "when": "hello" will match "hello"
* Strings will match using variables, "when": "my dog is ?name" will match "my dog is fido"
* Dictionaries will match a dictionary, "when": {"name": "fido"} will match {"name": "fido"}

## If the assertion matches, the "then" portion will fire
## Rules will "forward chain" - the "then" portion of rules will cause the engine to match against rules
    [
        {   "when": "hello",
            "then": {"user-intent": "greet"}
        },

        {   "when": {"user-intent": "greet"},
            "then": {"#output": "hello, world"}
        }
    ]

## You can have more than one command (action) in the "then" portion
    {   "when": "hello",
        "then": [{"#output": "hello there"}, 
                {"#output": "nice to meet you"}]
    }

## You can store "item" knowledge (facts)
    {"item": "user", "name": "jeremy", "dog": "fido"}

## You can reference the items (facts) and their properties in your rules,
## using $itemname.property syntax
    {"when": "what is my name",
    "then": [{"#output": "your name is $user.name"}
    }

## You can add your own or pip installed modules as plugins!

To do this, use load_plugin() and pass in a moniker and the "dot" path of the module. This module should already have been pip installed in the environment so that the runtime can load it, or could be a standalone module in your project.

    from thoughts.rules_engine import RulesEngine
    engine = RulesEngine()
    engine.load_plugin("#my-module", "my_module")

Then in your rules, you can use this as a command in the "then" rules.

Engine Methods
===================

## add_rule(rule)
Adds a rule into memory.

## load_rules(file)
Loads a .json rules file into memory.

## load_plugin(moniker, module_namespace)
Loads a plugin (Python module), which can be used in then "then "portion of rules. Whichever module you use will need to have a process function and that function will need to take two arguments - a dict and a thoughts.Context object.

my_module.py

    def process(command, context): 
        ...your logic here
        ...by convention, you can put the most relevant parameter feature into the head #my-module moniker,
        ...for example text = command["#my-module"]

Your custom module has access to the Context object, which contains all of the loaded rules and items from command that ran previously.

## run_assert(assertion)
Evaluates the assertion against the loaded rules. Essentially, the evaluation will attempt to match the assertion against the "when" portion of all loaded rules.

If a rule matches, then the engine will add the "then" portion of the rule to the engine's evaluation agenda, substituting any unification variables that were determined during the "when" matching stage into the "then" items, and then evaluting them one at a time.

As each command is evaluated for assertion, the system will also substitute any values from the Context Items that are indicated in the command item.

## run_console()
Runs a console input loop. Each item entered will be passed into the engine's run_assert(assertion) function for evaluation.

Entering "log" will display the debug log.

Entering "items" will display the Context Items.

Entering "exit" will exit the console loop. Note that the "exit" command is also passed in as an assertion one last time, in case you want to handle the exit event first in any rules.

Commands
===================

You can use commands in the "then" portion of your rules. The engine will run the commands if the "when" portion matches.

In this version, the following commands are available.

## #output
* Behavior: Will echo the text to the console (using print)
* Example: {"#output": "hello, world"}
* Optional: specifiy a "rate" to slow output the contents to the console

## #prompt
* Behavior: Will ask for input and store into an item
* Example: {"#input": "what is your name", "into": "username"}

## #read-rss
* Behavior: Will read the specified rss feed into an item
* Example: {"#read-rss": "https://rss-feed.rss", "into": "rss"}

## #load-json
* Behavior: Will read in a .json file into Context Items
* Example: {"#load-json": "filename.json", "into": "item-name"}

## #save-json
* Will save a Context Item into a .json file
* Example: {"#save-json": "filename.json", "from": "item-name"}

Examples
=====================

## read an rss feed and output it to the console at a readable rate
    [
        {"when": "rss digg.top",
        "then": [{"#read-rss": "$?feed", "into": "rss"},
                {"#output": "$rss.title", "rate": 0.0225}]
        },

        {"item": "digg", "top": "https://digg.com/rss/top.rss"}
    ]