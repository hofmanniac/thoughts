from thoughts.rules_engine import RulesEngine

def main():
    test_chatbot2()

def test_chatbot2():

    # start a new inference engine with sample rules
    engine = RulesEngine()

    basedir = "C:\\Users\\jeremyho\\source\\repos\\thoughts.chatbot"
    source_folder = basedir + "\\aiml\\pandorabots\\target"

    # engine.load_rules_from_file(source_folder + "\\bot_prop.json", name="bot_prop")
    # engine.load_rules_from_file(source_folder + "\\bot.json", name="bot")
    # engine.load_rules_from_file(source_folder + "\\condition.json", name="condition")
    # engine.load_rules_from_file(source_folder + "\\date.json", name="date")
    # engine.load_rules_from_file(source_folder + "\\person_sub.json", name="person_sub")
    # engine.load_rules_from_file(source_folder + "\\person.json", name="person")
    engine.load_rules_from_file(source_folder + "\\set_template.json", name="set_template")

    print("BOT: HI")

    agenda = []
    loop = True

    while (loop):

        console_input = input("YOU: ")
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

            if "#input" in agenda_item:
                agenda_item = agenda_item["#input"]

            elif type(agenda_item) is str:
                output_text = output_text + " " + agenda_item
                continue

            sub_result = engine.process_assertion(agenda_item)  

            if sub_result is None: continue
            for item in sub_result: agenda.append(item)

        output_text = str.strip(output_text)
        if len(output_text) > 0:
            output_command = {"#output": output_text, "rate": 0.05}
            engine.process_assertion(output_command)

def test_chatbot():

    # start a new inference engine with sample rules
    engine = RulesEngine()

    basedir = "C:\\Users\\jeremyho\\source\\repos\\thoughts.chatbot"
    source_folder = basedir + "\\aiml\\pandorabots\\target"
    # file = source_folder + "\\pattern.json"
    # engine.load_rules_from_file(source_folder + "\\bot_prop.json", name="bot_prop")
    # engine.load_rules_from_file(source_folder + "\\bot.json", name="bot")
    # engine.load_rules_from_file(source_folder + "\\condition.json", name="condition")
    # engine.load_rules_from_file(source_folder + "\\date.json", name="date")
    engine.load_rules_from_file(source_folder + "\\person_sub.json", name="person_sub")
    engine.load_rules_from_file(source_folder + "\\person.json", name="person")

    print("BOT: HI")

    agenda = []
    loop = True

    while (loop):

        console_input = input("YOU: ")
        console_input = str.upper(console_input)

        if (console_input == "CONTEXT"):
            print(engine.context.items)
            continue
        
        agenda.append(console_input)
        engine.clear_context_items()

        while(len(agenda) > 0):

            agenda_item = agenda.pop(0)

            if "#output" in agenda_item: 
                agenda_item["rate"] = .05
                print("BOT:", end=" ")

            sub_result = engine.process_assertion(agenda_item)
            
            if sub_result is None: continue
            for item in sub_result: agenda.append(item)

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