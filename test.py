from thoughts.rules_engine import RulesEngine

def main():
    # test()
    test_chatbot2()

def test():
    engine = RulesEngine()
    engine.load_rules_from_file("\\..\\rules\\context.json")
    # engine.process_assertion("test1")
    #engine.run_assert("test1")
    #engine.run_assert("test2 happy")
    # engine.run_assert("test3 dog")
    # engine.run_assert("test7 dog")
    engine.run_assert("test8 dog")

def test_chatbot2():

    # start a new inference engine with sample rules
    engine = RulesEngine()

    basedir = "C:\\Users\\jeremyho\\source\\repos\\thoughts.chatbot"
    source_folder = basedir + "\\aiml\\pandorabots\\target"

    engine.load_rules_from_file(source_folder + "\\bot_prop.json", name="bot_prop")
    engine.load_rules_from_file(source_folder + "\\bot.json", name="bot")
    engine.load_rules_from_file(source_folder + "\\condition.json", name="condition")
    engine.load_rules_from_file(source_folder + "\\date.json", name="date")
    engine.load_rules_from_file(source_folder + "\\person_sub.json", name="person_sub")
    engine.load_rules_from_file(source_folder + "\\person.json", name="person")
    engine.load_rules_from_file(source_folder + "\\set_template.json", name="set_template")
    engine.load_rules_from_file(source_folder + "\\star.json", name="star")
    engine.load_rules_from_file(source_folder + "\\formats.json", name="formats")
    engine.load_rules_from_file(source_folder + "\\first_rest.json", name="first_rest")
    engine.load_rules_from_file(source_folder + "\\state2capital_map.json", name="state2capital_map")
    engine.load_rules_from_file(source_folder + "\\map.json", name="map")
    engine.load_rules_from_file(source_folder + "\\input.json", name="input")

    print("BOT: HI")

    agenda = []
    loop = True

    while (loop):

        console_input = input("YOU: ")
        engine.process_assertion({"#store": console_input, "#push": "$input"})
        console_input = str.upper(console_input)

        if (console_input == "CONTEXT"):
            print(engine.context.items)
            continue
        
        input_command = {"#input": console_input}
        agenda.append(input_command)
        engine.clear_context_items()

        output_text = ""
        while(len(agenda) > 0):

            agenda_item = agenda.pop(0)

            if "#input" in agenda_item: agenda_item = agenda_item["#input"]

            elif type(agenda_item) is str:
                output_text = output_text + " " + agenda_item
                continue

            sub_result = engine.process_assertion(agenda_item)  

            if sub_result is None: continue

            idx = 0
            for item in sub_result:
                agenda.insert(idx,item)
                idx = idx + 1

        output_text = str.strip(output_text)
        if len(output_text) > 0:
            output_command = {"#output": "BOT: " + output_text, "rate": 0.05}
            engine.process_assertion(output_command)

def test_engine():
    pass

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
    # engine.load_rules_from_file("\\..\\rules\\test.json", name="test")
    # engine.run_console()

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
    # twine upload --repository-url https://test.pypi.org/legacy/ dist/*0.1.6*
    # Check in to Github
    # twine upload dist/*0.1.6*

main()