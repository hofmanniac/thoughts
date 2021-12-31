import json
import os
from thoughts.context import Context
# import thoughts.unification
import copy
# from thoughts.commands import assert_command

class RulesEngine:

    context = Context()
    # log = []
    _agenda = []
    _plugins = {}
    # _arcs = []

    def __init__(self):
        
        self.context = Context()
        self._agenda = []
        self._load_plugins()

        # add the default ruleset
        self.context.rulesets.append({"name": "default", "rules": []})
        self.context.default_ruleset = self.context.rulesets[0]

    def load_plugin(self, moniker, dotpath):
        plugin_module = __import__(dotpath, fromlist=[''])
        self._plugins[moniker]  = plugin_module

    def clear_rules(self):
        """Clears all rules from the engine."""

        self.context.rulesets = []

    # add a new rule manually
    def add_rule(self, rule):
        self.context.add_rule(rule)

    def add_rules(self, rules: list, name: str = None, path: str = None):
        self.context._add_rules(rules, name, path)

    # load rules from a .json file
    def load_rules_from_file(self, file, name = None):
        
        if (file.startswith("\\")):
            dir = os.path.dirname(__file__)
            file = dir + file

        with open(file) as f:
            file_rules = list(json.load(f))
            self.context._add_rules(file_rules, name, file)
            print("loaded", len(file_rules), "rules")

    def load_rules_from_list(self, rules, name = None):
        self.context.log_message("LOAD:\t" + str(len(rules)))
        self.context._add_rules(rules, name, None)

    def clear_arcs(self):
        self._arcs = []

    def clear_context_variables(self):
        self.context.clear_variables()

    def extract_leaf_nodes(self, tree):
        
        if type(tree) is not list: tree = [tree]

        leafs = []

        def _get_leaf_nodes(node):
            if node is not None:
                if "#conclusions" in node and node["#conclusions"] is not None:
                    if len(node["#conclusions"]) > 0:
                        new_node = copy.deepcopy(node)
                        del new_node["#conclusions"]
                        leafs.append(new_node)
                    for n in node["#conclusions"]:
                        _get_leaf_nodes(n)
        
        for tree_node in tree:
            _get_leaf_nodes(tree_node)

        return leafs

    def process2(self, assertions):
        if type(assertions) is not list: assertions = [assertions]

        loop = True
        while loop:
            assertion = self.find_next(assertions)
            conclusions = self._process_single(assertion)
            assertion["#conclusions"] = conclusions
            if conclusions is not None: loop = False
        return assertions

    def find_next(self, assertions):
        for assertion in assertions:
            if "#conclusions" not in assertion: 
                return assertion
            else:
                if assertion["#conclusions"] is not None:
                    next = self.find_next(assertion["#conclusions"])
                    if next is not None: return next

    def process_tree(self, assertions):
    
        results = []

        if type(assertions) is not list:
            assertions = [assertions]

        for assertion in assertions:
            sub_result = self._process_single(assertion)

            if sub_result is not None:
                sub_result = self.process_tree(sub_result)

            new_result = copy.deepcopy(assertion)
            if type(new_result) is not dict: new_result = {"#assertion": new_result} 
            new_result["#conclusions"] = sub_result
            results.append(new_result)

        return results

    def process(self, assertions):
       
        agenda = []
        conclusions = []

        if type(assertions) is not list: agenda = [assertions]
        else: agenda = assertions

        while(len(agenda) > 0):

            agenda_item = agenda.pop(0)

            if type(agenda_item) is list:
                agenda = agenda_item + agenda
                continue
            
            sub_result = self._process_single(agenda_item)
            
            if sub_result is not None and len(sub_result) > 0:

                agenda.insert(0, sub_result)
                sub_conclusions = copy.deepcopy(sub_result)
                
                if len(sub_conclusions) == 1: sub_conclusions = sub_conclusions[0]
                conclusions.append(sub_conclusions)

                # conclusion = copy.deepcopy(agenda_item)
                # conclusion["#conclusions"] = sub_conclusions
                # conclusions.append(conclusion)
                

        return conclusions

    # def process2(self, assertions):
    #     """Processes the assertions and any resulting assertions until no additional assertions are generated.
        
    #     Returns assertions that were generated and have already been processed."""

    #     conclusions = []
    #     sub_results = assertions

    #     while len(sub_results) > 0:

    #         sub_results = self.process_single_cycle(sub_results)

    #         if len(sub_results) > 0: 
    #             sub_conclusions = copy.deepcopy(sub_results)
    #             conclusions.append(sub_conclusions)

    #     return conclusions

    # def process_single_cycle(self, assertions):
    #     """Processes the assertions through a single rule-match cycle.

    #     Returns assertions that were generated and that need processed."""
        
    #     agenda = []
    #     conclusions = []

    #     if type(assertions) is not list: agenda = [assertions]
    #     else: agenda = assertions

    #     while(len(agenda) > 0):

    #         agenda_item = agenda.pop(0)

    #         if type(agenda_item) is not list:
    #             sub_result = self._process_single(agenda_item)
    #         else:
    #             sub_result = self.process(agenda_item)
            
    #         if sub_result is not None and len(sub_result) > 0:
    #             agenda.insert(0, sub_result)
    #             sub_conclusions = copy.deepcopy(sub_result)
    #             conclusions.extend(sub_conclusions)

    #     return conclusions

    def _process_single(self, assertion):

        self.context.log_message("")
        self.context.log_message("ASSERT:\t" + str(assertion))

        if (type(assertion) is str):
            if (assertion.startswith("{")):
                assertion = json.loads(assertion)

        # apply $ items from context
        assertion = self.context.apply_values(assertion, self.context)

        command = None
        if (type(assertion) is dict): command = self._parse_command_name(assertion)
        
        if command is None: command = "#assert"
        else: assertion = self._apply_commands(assertion)

        result = self._call_plugin(command, assertion)
        return result

    # def _process_assertion(self, assertion):
        
    #     result = []

    #     assertions = None
    #     if type(assertion) is not list: assertions = [assertion]
    #     else: assertions = assertion

    #     for assertion in assertions:

    #         self.context.log_message("")
    #         self.context.log_message("ASSERT:\t" + str(assertion))

    #         # apply $ items from context
    #         assertion = self.context.apply_values(assertion, self.context)

    #         command = None
    #         if (type(assertion) is dict): command = self._parse_command_name(assertion)
            
    #         if command is None: command = "#assert"
    #         else: 
    #             assertion = self._apply_commands(assertion)

    #         sub_result = self._call_plugin(command, assertion)
    #         result = self.context.merge_into_list(result, sub_result)
        
    #     return result

    #    # run the assertion - match and fire rules
    # def _run_assert(self, assertion):

    #     # parse json-style string assertion into dict
    #     if (type(assertion) is str):
    #         if (assertion.startswith("{")):
    #             assertion = json.loads(assertion)

    #     if type(assertion) is list:
    #         self._agenda.extend(assertion)

    #     # add assertion to the agenda
    #     self._agenda.append(assertion)

    #     # process the agenda (until empty)
    #     self.process_agenda()

    # def _process_agenda(self):

    #     # while the agenda has items
    #     while(len(self._agenda) > 0):

    #         # grab the topmost agenda item
    #         agenda_item = self._agenda.pop(0)

    #         # process it
    #         sub_result = self.process_assertion(agenda_item)
            
    #         if sub_result is None: continue
    #         for item in sub_result: self._agenda.append(item)

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

                self.process(assertion)

                if (assertion == "#exit"): loop = False
            
            except:
                print("Error")

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
    
    def _apply_commands(self, term, eval = False):       
        if type(term) is dict:
            result = {}
            for key in term.keys():
                if eval == True:
                    if key == "#replace":
                        new_val = self._call_plugin(key, term)
                        return new_val
                    else:
                        new_val = self._apply_commands(term[key], eval=True)
                else:
                    new_val = self._apply_commands(term[key], eval=True)
                result[key] = new_val
            return result           
        return term

    def _parse_command_name(self, assertion):

        # grab the first where key starts with hashtag (pound)
        for key in assertion.keys(): 
            if key == "#append": continue
            if key == "#into": continue
            if key == "#push": continue
            if key == "#unification": continue
            if key == "#seq-start": continue
            if key == "#seq-end": continue
            if key.startswith("#"): return key
