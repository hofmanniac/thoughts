from thoughts.rules_engine import RulesEngine

# pip install twine
# pip install wheel

# update version in setup.py
# update version in all __init__.py files (2 places)
# update version number below (2 places)
# python setup.py sdist bdist_wheel
# twine upload --repository-url https://test.pypi.org/legacy/ dist/*0.1.6*
# Check in to Github
# twine upload dist/*0.1.6*

engine = RulesEngine()

def test_chatbot():

    # start a new inference engine with sample rules
    engine = RulesEngine()

    basedir = "my_repo_location\\repos\\thoughts.chatbot"

    # sample_folder = basedir + "\\aiml\\single"
    # engine.load_rules_from_file(sample_folder + "\\sample.json", name="sample")

    source_folder = basedir + "\\aiml\\pandorabots\\target"
    engine.load_rules_from_file(source_folder + "\\bot_prop.json", name="bot_prop")
    # engine.load_rules_from_file(source_folder + "\\bot.json", name="bot")
    # engine.load_rules_from_file(source_folder + "\\condition.json", name="condition")
    # engine.load_rules_from_file(source_folder + "\\date.json", name="date")
    # engine.load_rules_from_file(source_folder + "\\first_rest.json", name="first_rest")
    # engine.load_rules_from_file(source_folder + "\\formats.json", name="formats")
    # engine.load_rules_from_file(source_folder + "\\input.json", name="input")
    # engine.load_rules_from_file(source_folder + "\\map.json", name="map")
    # engine.load_rules_from_file(source_folder + "\\pattern.json", name="pattern")
    # engine.load_rules_from_file(source_folder + "\\topic.json", name="topic")
    # engine.load_rules_from_file(source_folder + "\\that.json", name="that")
    engine.load_rules_from_file(source_folder + "\\person_sub.json", name="person_sub")
    # engine.load_rules_from_file(source_folder + "\\person.json", name="person")
    # engine.load_rules_from_file(source_folder + "\\set_template.json", name="set_template")
    # engine.load_rules_from_file(source_folder + "\\srai.json", name="srai")
    # engine.load_rules_from_file(source_folder + "\\star.json", name="star")
    # engine.load_rules_from_file(source_folder + "\\state2capital_map.json", name="state2capital_map")
    # engine.load_rules_from_file(source_folder + "\\think.json", name="think")
    
    engine.load_rules_from_file(basedir + "\\aiml\\alice\\pickup.json", name="pickup")
    engine.load_rules_from_file(basedir + "\\aiml\\alice\\atomic.json", name="atomic")
    engine.load_rules_from_file(basedir + "\\aiml\\alice\\date.json", name="date")
    engine.load_rules_from_file(basedir + "\\aiml\\alice\\knowledge.json", name="knowledge")
    engine.load_rules_from_file(basedir + "\\aiml\\alice\\gossip.json", name="gossip")
    engine.load_rules_from_file(basedir + "\\aiml\\alice\\biography.json", name="biography")
    engine.load_rules_from_file(basedir + "\\aiml\\alice\\xfind.json", name="xfind")
    engine.load_rules_from_file(basedir + "\\aiml\\alice\\inquiry.json", name="inquiry")
    engine.load_rules_from_file(basedir + "\\aiml\\alice\\imponderables.json", name="imponderables")
    # engine.load_rules_from_file(basedir + "\\aiml\\alice\\ai.json", name="ai")
    # engine.load_rules_from_file(basedir + "\\aiml\\alice\\alice.json", name="alice")
    # engine.load_rules_from_file(basedir + "\\aiml\\alice\\client_profile.json", name="client_profile")
    # engine.load_rules_from_file(basedir + "\\aiml\\alice\\reduction4.safe.json", name="reduction4.safe")
    # engine.load_rules_from_file(basedir + "\\aiml\\alice\\bot_profile.json", name="bot_profile")
    engine.load_rules_from_file(basedir + "\\aiml\\alice\\update1.json", name="update1")
    engine.load_rules_from_file(basedir + "\\aiml\\alice\\personality.json", name="personality")

    print("BOT: HI")

    agenda = []
    loop = True

    while (loop):

        console_input = input("YOU: ")

        if (str.upper(console_input) == "CONTEXT"):
            engine.context.print_items()
            continue
        elif (str.upper(console_input) == "DEBUG"):
            engine.context.display_log = not engine.context.display_log
            if engine.context.display_log == True: print("debug is now on")
            else: print("debug is now off")
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
                if agenda_item == "." or agenda_item == "!" or agenda_item == "?":
                    output_text = output_text + agenda_item
                elif len(agenda_item) > 0:
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

        # store $that
        that_text = output_text.replace("?", "")
        that_text = that_text.replace("!", "")
        store_command = {"#store": that_text, "#into": "$that"}
        engine.process_assertion(store_command)

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
