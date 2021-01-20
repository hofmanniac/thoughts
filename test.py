from thoughts.rules_engine import RulesEngine

def main():
 
    # test_replace()
    # test()
    test_chatbot()

def test():

    engine = RulesEngine()

    # engine.load_rules_from_file("\\..\\rules\\context.json")
    # # engine.process_assertion("test1")
    # #engine.run_assert("test1")
    # #engine.run_assert("test2 happy")
    # # engine.run_assert("test3 dog")
    # # engine.run_assert("test7 dog")
    # engine.run_assert("test8 dog")

    engine.load_rules_from_file("\\..\\rules\\regression1.json")
    engine.run_assert("test1")
    engine.run_assert("test2 pass")
    engine.run_assert("test3 pass")

def test_chatbot():

    # start a new inference engine with sample rules
    engine = RulesEngine()

    basedir = "C:\\Users\\jeremyho\\source\\repos\\thoughts.chatbot"
    source_folder = basedir + "\\aiml\\pandorabots\\target"

    # engine.load_rules_from_file(source_folder + "\\bot_prop.json", name="bot_prop")
    # engine.load_rules_from_file(source_folder + "\\bot.json", name="bot")
    # engine.load_rules_from_file(source_folder + "\\condition.json", name="condition")
    # engine.load_rules_from_file(source_folder + "\\date.json", name="date")
    # engine.load_rules_from_file(source_folder + "\\first_rest.json", name="first_rest")
    # engine.load_rules_from_file(source_folder + "\\formats.json", name="formats")
    # engine.load_rules_from_file(source_folder + "\\input.json", name="input")
    # engine.load_rules_from_file(source_folder + "\\map.json", name="map")
    # engine.load_rules_from_file(source_folder + "\\pattern.json", name="pattern")

    engine.load_rules_from_file(source_folder + "\\person_sub.json", name="person_sub")
    # engine.load_rules_from_file(source_folder + "\\person.json", name="person")

    # engine.load_rules_from_file(source_folder + "\\set_template.json", name="set_template")
    # engine.load_rules_from_file(source_folder + "\\srai.json", name="srai")
    # engine.load_rules_from_file(source_folder + "\\star.json", name="star")
    # engine.load_rules_from_file(source_folder + "\\state2capital_map.json", name="state2capital_map")
    # engine.load_rules_from_file(source_folder + "\\think.json", name="think")
    
    # engine.load_rules_from_file(basedir + "\\aiml\\alice\\atomic.json", name="atomic")
    # engine.load_rules_from_file(basedir + "\\aiml\\alice\\knowledge.json", name="knowledge")
    # engine.load_rules_from_file(basedir + "\\aiml\\alice\\gossip.json", name="gossip")

    engine.load_rules_from_file(basedir + "\\aiml\\alice\\biography.json", name="biography")
    engine.load_rules_from_file(basedir + "\\aiml\\alice\\xfind.json", name="xfind")
    engine.load_rules_from_file(basedir + "\\aiml\\alice\\pickup.json", name="pickup")

    engine.load_rules_from_file(basedir + "\\aiml\\alice\\ai.json", name="ai")

    print("BOT: HI")

    agenda = []
    loop = True

    while (loop):

        console_input = input("YOU: ")

        if (str.upper(console_input) == "CONTEXT"):
            print("==================================")
            for key in engine.context.items.keys():
                print(key + ":", engine.context.items[key])
                # if type(engine.context.items[key]) is list:
                #     print(key + ":")
                #     idx = 0
                #     for item in engine.context.items[key]:
                #         print("[" + str(idx) + "] ", item)
                #         idx = idx + 1
                # else:
                #     print(key + ":", engine.context.items[key])
                # print("")
            print("==================================")
            continue

        engine.process_assertion({"#store": console_input, "#push": "$input"})
        console_input = str.upper(console_input)
     
        input_command = {"#input": console_input}
        agenda.append(input_command)
        engine.clear_context_variables()

        output_text = ""
        while(len(agenda) > 0):

            agenda_item = agenda.pop(0)

            is_input = False
            if "#input" in agenda_item: 
                agenda_item = agenda_item["#input"]
                is_input = True
            elif type(agenda_item) is str:
                output_text = output_text + " " + agenda_item
                continue

            # add rates to outputs
            sub_result = engine.process_assertion(agenda_item)  

            if sub_result is None or len(sub_result) == 0:
                if is_input == True:              
                    no_match = {"#assert": {"#no-match": console_input}}
                    sub_result = engine.process_assertion(no_match)
                if sub_result is None: continue

            idx = 0
            for item in sub_result:
                agenda.insert(idx,item)
                idx = idx + 1

        output_text = str.strip(output_text)
        if len(output_text) == 0: continue

        # normally this is handled by the engine, but we want to get consistent values
        output_text = engine.context.apply_values(output_text, engine.context)

        output_command = {"#output": "BOT: " + output_text, "rate": 0.05}
        engine.process_assertion(output_command)

        store_command = {"#store": output_text, "#push": "$response"}
        engine.process_assertion(store_command)

# def add_rates(assertion):
#     if type(assertion) is dict:
#         new_dict = {}
#         for key in assertion.keys():
#             if key == "#output": 
#                 new_dict["rate"] = 0.05
#                 new_dict["#output"] = assertion[key]
#             else:
#                 new_dict[key] = add_rates(assertion[key])
#         assertion = new_dict
#     elif type(assertion) is list:
#         new_list = []
#         for item in assertion: 
#             new_list.append(add_rates(item))
#         assertion = new_list
#     return assertion

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

def test_replace():

    from thoughts.commands import replace

    withset = {
        "with you": "with me", 
        "with me": "with you", 
        "me": "you", 
        "you": "me", 
        "i": "you",
        "am": "are", 
        "are": "am"}

    text = "i am with you on that one"

    engine = RulesEngine()
    engine.context.items["test"] = withset

    replace_command = {"#replace": text, "with": "test"}
    result = replace.process(replace_command, engine.context)
    print(result)

main()