import json
import os
from thoughts.context import Context
# import thoughts.unification
# import copy
# from thoughts.commands import assert_command

class RulesEngine:

    #region Class Variables

    context = Context()
    # log = []
    _agenda = []
    _plugins = {}
    # _arcs = []

    #endregion

    #region Constructor

    def __init__(self):
        self._load_plugins()

        # add the default ruleset
        self.context.rulesets.append({"name": "default", "rules": []})
        self.context.default_ruleset = self.context.rulesets[0]
        
    #endregion

    #region Plugins

    def load_plugin(self, moniker, dotpath):
        plugin_module = __import__(dotpath, fromlist=[''])
        self._plugins[moniker]  = plugin_module

    def _load_plugins(self):
        self.load_plugin("#assert", "thoughts.commands.assert_command")
        self.load_plugin("#output", "thoughts.commands.output")
        self.load_plugin("#prompt", "thoughts.commands.prompt") 
        self.load_plugin("#read-rss", "thoughts.commands.read_rss")    
        self.load_plugin("#load-json", "thoughts.commands.load_json")  
        self.load_plugin("#save-json", "thoughts.commands.save_json") 
        self.load_plugin("#tokenize", "thoughts.commands.tokenize") 
        self.load_plugin("#lookup", "thoughts.commands.lookup")
        self.load_plugin("#random", "thoughts.commands.random")
        self.load_plugin("#store", "thoughts.commands.store")
        self.load_plugin("#replace", "thoughts.commands.replace")
        self.load_plugin("#switch", "thoughts.commands.switch")
        self.load_plugin("#date", "thoughts.commands.date")
        self.load_plugin("#format", "thoughts.commands.format")
        self.load_plugin("#first", "thoughts.commands.first")
        self.load_plugin("#rest", "thoughts.commands.rest")

    def _call_plugin(self, moniker, assertion):

        if moniker in self._plugins:       
            plugin = self._plugins[moniker]
            new_items = plugin.process(assertion, self.context)
            return new_items

        if (moniker == '#clear-arcs'): self.clear_arcs()

    #endregion

    # load rules from a .json file
    def load_rules_from_file(self, file, name = None):
        
        if (file.startswith("\\")):
            dir = os.path.dirname(__file__)
            file = dir + file

        with open(file) as f:
            file_rules = list(json.load(f))
            self.context.add_ruleset(file_rules, name, file)

    def load_rules_from_list(self, rules, name = None):

        self.log_message("LOAD:\t" + str(len(rules)))
        self.context.add_ruleset(rules, name, None)

    # add a new rule manually
    def add_rule(self, rule):
        self.context.default_ruleset["rules"].append(rule)

    def clear_arcs(self):
        self._arcs = []

    def _parse_command_name(self, assertion):

        # grab the first where key starts with hashtag (pound)
        for key in assertion.keys(): 
            if key == "#append": continue
            if key == "#into": continue
            if key == "#push": continue
            if key == "#unification": continue
            if key.startswith("#"): return key

    def clear_context_variables(self):
        self.context.clear_variables()

    def process_assertion(self, assertion):
        
        result = []

        assertions = None
        if type(assertion) is not list: assertions = [assertion]
        else: assertions = assertion

        for assertion in assertions:

            self.context.log_message("")
            self.context.log_message("ASSERT:\t\t" + str(assertion))

            # apply $ items from context
            assertion = self.context.apply_values(assertion, self.context)

            command = None
            if (type(assertion) is dict): command = self._parse_command_name(assertion)
            if command is None: command = "#assert" #assertion = {"#assert": assertion}

            sub_result = self._call_plugin(command, assertion)
            result = self.context.merge_into_list(result, sub_result)
        
        return result
            
    # run the assertion - match and fire rules
    def run_assert(self, assertion):

        # parse json-style string assertion into dict
        if (type(assertion) is str):
            if (assertion.startswith("{")):
                assertion = json.loads(assertion)

        # add assertion to the agenda
        self._agenda.append(assertion)

        # process the agenda (until empty)
        self.process_agenda()

    def process_agenda(self):

        # while the agenda has items
        while(len(self._agenda) > 0):

            # grab the topmost agenda item
            agenda_item = self._agenda.pop(0)

            # process it
            sub_result = self.process_assertion(agenda_item)
            
            if sub_result is None: continue
            for item in sub_result: self._agenda.append(item)

    def run_console(self):
        """ 
        Runs a console input and output loop, asserting the input.
        Use '#log' to output the engine log.
        Use '#items' to output the items from the engine context.
        Use '#clear-arcs' to clear the active rules (arcs).
        Use '#exit' to exit the console loop.
        """

        loop = True

        while loop:

            try:
                # enter an assertion below
                # can use raw text (string) or can use json / dict format
                assertion = input(": ")

                if (assertion == "#log"):
                    print("")
                    print("log:")
                    print("------------------------")
                    for item in self.log: print(item)
                    continue

                elif (assertion == "#items"):
                    print("")
                    print("context items:")
                    print("------------------------")
                    for item in self.context.items: 
                        print(str(item))
                    continue
                
                elif (assertion == "#clear-arcs"):
                    self.clear_arcs()

                self.run_assert(assertion)

                if (assertion == "#exit"): loop = False
            
            except:
                print("Error")
