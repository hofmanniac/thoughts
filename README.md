# Thoughts Rules Engine

Thoughts is a lightweight inference engine.

# How To Use

pip install thoughts

Check out the notebooks folder for tutorials and ideas of what you can do with the engine.

[Tutorials](https://github.com/hofmanniac/thoughts/tree/master/notebooks/tutorial)

```python
from thoughts.rules_engine import RulesEngine

# start a new engine
engine = RulesEngine()

# define your rules
rule = {"#when": "test",
        "#then": {"#output": "hello, world!"} }

# load the rules into the engine
engine.add_rule(rule)

# run assertions against those rules
result = engine.process("test")
print(result)

PRINTS:
['hello, world!']
```

# What's New

## Next Release

Rebuilt the assertion logic agenda to use tree rather than a stack. This allows for tracking exactly how each conclusion was generated and later for depth-first and breadth-first search options and other assertion strategies.

Ability to allow junk in sequence detection.

Ability to allow set detection.

## Release (0.1.6)

You can now load multiple rule sets into the Context. Each rules set can have a name. If you don't provide a name, the system will generate a unique identifier (GUID) upon import.

You can also now load rules from a list. For this reason, load_rules has been renamed to load_rules_from_file.

New rules that you add through add_rule are added to a rule set called "default". Future release may allow you to change where new rules are added.

Finally, the Console will trap errors and report a simple "Error". Future releases may improve this with more information.

## Thu Dec-24, 2020 Release (0.1.5)

Minor update - Added #assert command, to more directly indicate when an assertion should be performed.

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
