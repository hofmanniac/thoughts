# Thoughts Rules Engine

Thoughts is a lightweight rules engine.

# What's New

## Release (0.1.6)

You can now load multiple rule sets into the Context. Each rules set can have a name. If you don't provide a name, the system will generate a unique identifier (GUID) upon import.

You can also now load rules from a list. For this reason, load_rules has been renamed to load_rules_from_file.

New rules that you add through add_rule are added to a rule set called "default". Future release may allow you to change where new rules are added.

Finally, the Console will trap errors and report a simple "Error". Future releases may improve this with more information.

## Thu Dec-24, 2020 Release (0.1.5)

Minor update - Added #assert command, to more directly indicate when an assertion shoudl be performed.

## Thu Dec-24, 2020 Release (0.1.4)

Minor update - Fixed #replace to process replacments token by token (separated by spaces).

## Tue Dec-22, 2020 Release (0.1.2)

Lots of improvements in this latest release - mostly geared towards supporting chatbots but can also be used for other types of applications and logic.

Added #append and #into in-line commands. If these are present in your command, then the engine will store the result of the command (if present) into the variable specified. If #into is used, the variable will be set. If #append is used, the variable will be appended to the existing variable, or set if there is no existing variable already.

Added #store command to store a value into a context item.

Added #replace to substitute word tokens (separated by spaces) in the specified value, with the keys specified in the "with" argument. This is useful in scenarios where you want to substitute words like "you" with "me" or other straightforward (key matching) substitutions.

Items should now use the #item tag instead of "item" (without the hashtag). This is to keep the engine-aware tags using the hashtag designation to avoid collisions and to provide some optimizations.

## Tue Dec-22, 2020 Release (0.1.1)

A new command has been added, #random.

#random will take a list of commands and randomly choose from that set. For example, you could use this in a chatbot scenario to vary the responses from a set of possible responses.

## Wed Dec-16, 2020 Release (0.1.0) - Beta!

Excited to release some rule enhancements to allow for some more advanced natural language processing capabilities. Now you can use #combine in the "then" portion (consequent) of your rules to combine multiple unification variables into a single dict object.

Check out the sample at https://github.com/hofmanniac/thoughts/tree/master/samples/nlp/nlp_head_grammar.json for an example of how to parse a simple "EFFECT because CAUSE" type statement using syntax and semantics in tandem.

Also now that the engine is at a decent point in terms of capability, bumping the release number up a bit. Consider this as the first Beta version!

## Mon Dec-14, 2020 Release (0.0.7)

Added a sample for calculating Winograd Schema information with light natural language parsing. Also now the "then" portions of rules will push items to the top of the agenda, and in order. This will help favor new rules to finish their forward chaining behaviors sooner.

See winograd_1.json in https://github.com/hofmanniac/thoughts/tree/master/samples/academic/winograd for an example.

## Sun Dec-13, 2020 Release (0.0.6)

You can now #tokenize a string and apply an assertion for every token in the string. You can also now use #lookup, to locate a matching fact in the context, which will then assert the matching fact. This is useful in parsing natural language, where you want to assert each word (token) in a sentence, lookup the corresponding lemma, and then match against a set of rules.

See sequence_nlp.json in https://github.com/hofmanniac/thoughts/tree/master/samples/nlp for an example in action.

Moved apply_unification from engine into thoughts.unification. Seemed the more natural spot!

## Sat Dec-12, 2020 Release (0.0.5)

You can now create sequence-based rules, which wait for multiple assertions in sequence before firing. See the How to Use section below for more details.

## Sun Nov-29, 2020 Release (0.0.4)

In this release, you can now load and save .json files into Context Items. See #load-json and #save-json in the Commands section below for more information.

## Sat Nov-28, 2020 Release (0.0.3)

In this release, you can now load custom plugins for use in the "then" portion of rules. See "load_plugin" in the Engine Methods section below for more information.

# How To Use

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
    engine.load_rules_from_file("rules.json")

## Alternatively, you can create a manual rule without loading a file

    rule = {"when": "what time is it", "then": {"#output": "time to get a new watch"}}
    engine.add_rule(rule)

## Define and run assertions

    assertion = "hello"
    engine.run_assert(assertion)

## Assertions will match the "when" portion of rules, based on a unification algorithm:

- Strings will match direct string matches, "when": "hello" will match "hello"
- Strings will match using variables, "when": "my dog is ?name" will match "my dog is fido"
- Dictionaries will match a dictionary, "when": {"name": "fido"} will match {"name": "fido"}

## If the assertion matches, the "then" portion will fire

Rules will "forward chain" - the "then" portion of rules will cause the engine to match against rules
[
{ "when": "hello",
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

## You can reference the items (facts) and their properties in your rules, using $itemname.property syntax

    {"when": "what is my name",
    "then": [{"#output": "your name is $user.name"}
    }

## You can use sequence-based rules (chart parsing)

This is useful for natural-language type parsing where a rule needs to wait on input before firing the consequent (then) portion. In the example below, when {"cat": "art", "lemma": "the"} is asserted, the rule will match the first constituent and add the rule as an arc to the active arcs. The new arc will "wait" for another consituent with {"cat": "n", "lemma": "..."} to be asserted before matching and firing the "then" portion. Be sure to place the constituents within an array / list [] within the "when" portion.

    {   "when": [
            {"cat" :"art", "lemma": "?det"},
            {"cat" :"n", "lemma": "?entity"}],
        "then":
            {"cat": "np", "entity": "?entity", "art": "?art"}
    }

Note - The active rules (arcs) will remain in memory until you clear them using engine.clear_arcs(). This is useful to assert one constituent at a time into the engine to inspect the results.

## You can add your own or pip installed modules as plugins!

To do this, use load_plugin() and pass in a moniker and the "dot" path of the module. This module should already have been pip installed in the environment so that the runtime can load it, or could be a standalone module in your project.

    from thoughts.rules_engine import RulesEngine
    engine = RulesEngine()
    engine.load_plugin("#my-module", "my_module")

Then in your rules, you can use this as a command in the "then" rules.

# Engine Methods

## add_rule(rule)

Adds a rule into memory. New rules are added to the default ruleset.

## clear_arcs()

Clears all active arcs (sequence rules in-progress) from memory.

## load_rules_from_file(file, name=None)

Loads a .json rules file into memory.

## load_rules_from_list(rules, name=None)

Loads rules into memory directly from a list.

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

Entering "#log" will display the debug log.

Entering "#items" will display the Context Items.

Entering "#clear_arcs" will clear any active sequence-based rules (arcs) from memory.

Entering "#exit" will exit the console loop. Note that the "#exit" command is also passed in as an assertion one last time, in case you want to handle the exit event first in any rules.

# Commands

You can use commands in the "then" portion of your rules. The engine will run the commands if the "when" portion matches.

## assert

Will assert a value to the engine.

    {"#assert": "Hello, World"}

## #output

Will echo the text to the console (using print)

Optional: specifiy a "rate" to slow output the contents to the console

    {"#output": "hello, world"}

## #prompt

Will ask for input and store into an item

    {"#input": "what is your name", "into": "username"}

## #random

Will randomly assert from a set of possible options

    {"when": "greet me",
     "then": {"#random": [
         {"#output": "Hi"},
         {"#output": "Hello"},
         {"#output": "What's up?"},
         {"#output": "How are you?"}
     ]}
    }

## #read-rss

Will read the specified rss feed into an item

    {"#read-rss": "https://rss-feed.rss", "into": "rss"}

## #load-json

Will read in a .json file into Context Items

    {"#load-json": "filename.json", "into": "item-name"}

## #lookup

Will match (through unification) items in the context. If found, will assert the matching item.

    {"#lookup": {"lemma": "dog"}}

## #replace

Will substitute word tokens (separated by spaces) in the specified value, with the keys specified in the "with" argument. This is useful in scenarios where you want to substitute words like "you" with "me" or other straightforward (key matching) substitutions.

    [
        {   "when": "test replace",
            "then": [{"#replace": "you like me", "with": "$pronouns", "#into": "?output"},
                    {"#output": "?output"} ]
        },

        {"#item": "pronouns", "me": "you", "you": "me", "i": "you"}
    ]

    Console Result: i like you

## #save-json

Will save a Context Item into a .json file

    {"#save-json": "filename.json", "from": "item-name"}

## #store

Stores a value into a context item. Use #into to start a new variable or to overwrite any existing values. Use #append to append to an existing value (or to start a new variable).

    [
        {   "when": "my name is "?name",
            "then": [{"#store": "?name", ", "#into": "?username"}]
        }
    ]

## #tokenize

Will split a string into tokens (separated by spaces) and then assert each into the form specified in the "assert" argument

    {"#tokenize": "?text", "assert": {"#lookup": {"lemma": "#"}}}
