from thoughts.rules_engine import RulesEngine

# start a new inference engine with sample rules
engine = RulesEngine()

# engine.add_rule('{"when": "test", "then": {"#output": "hello!"} }')
# engine.run_assert("test")

# engine.load_rules("\\..\\rules\\rules.json")
# engine.load_rules("\\..\\samples\\hello_world.json")
# engine.load_rules("\\..\\samples\\choose_your_own_adventure.json")
# engine.load_rules("\\..\\samples\\sequence_nlp.json")
# engine.load_rules("\\..\\samples\\academic\winograd\winograd_1.json")
# engine.load_rules("\\..\\samples\\unification.json")
# engine.load_rules("\\..\\rules\\nlp_head_grammar.json")
# engine.load_rules("\\..\\rules\\merge_unification.json")
# engine.load_rules("\\..\\samples\\academic\\squad\\ipcc.json")
engine.load_rules("\\..\\rules\\test.json")

engine.run_console()

# # create a manual rule
# rule = {"when": "what time is it", "then": "time to get a new watch"}
# engine.add_rule(rule)

# # run an assertion
# engine.run_assert("what time is it")

# pip install twine
# pip install wheel

# update version in setup.py
# update version in all __init__.py files (2 places)
# update version number below (2 places)
# python setup.py sdist bdist_wheel
# twine upload --repository-url https://test.pypi.org/legacy/ dist/*0.1.2*
# Check in to Github
# twine upload dist/*0.1.2*