from thoughts.rules_engine import RulesEngine

# start a new inference engine with sample rules
engine = RulesEngine()

# engine.load_rules("\\..\\rules\\rules.json")
engine.load_rules("\\..\\samples\\hello_world.json")
# engine.load_rules("\\..\\samples\\choose_your_own_adventure.json")

engine.run_console()

# while True:

#     # enter an assertion below
#     # can use raw text (string) or can use json / dict format
#     assertion = input(": ")

#     if (assertion == "log"):
#         print("")
#         print("log:")
#         print("------------------------")
#         for item in engine.log: print(item)
#         continue

#     elif (assertion == "items"):
#         print("")
#         print("context items:")
#         print("------------------------")
#         for item in engine.context.items: 
#             print(str(item))
#         continue

#     # engine.run_assert("hello")
#     engine.run_assert(assertion)

# # create a manual rule
# rule = {"when": "what time is it", "then": "time to get a new watch"}
# engine.add_rule(rule)

# # run an assertion
# engine.run_assert("what time is it")

# pip install twine
# pip install wheel

# update version in setup.py
# update version in all __init__.py files (2 places)
# update version number below
# python setup.py sdist bdist_wheel
# twine upload --repository-url https://test.pypi.org/legacy/ dist/*0.0.3*
# twine upload dist/*0.0.3*