import json
import os
from thoughts.context import Context
import thoughts.unification
import copy

class RulesEngine:

    #region Class Variables

    context = Context()
    log = []
    _agenda = []
    _plugins = {}
    _arcs = []

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

    #endregion

    def log_message(self, message):
        self.log.append(message)

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

    # process the 'then' portion of the rule
    def _process_then(self, rule, unification):
    
        result = []
        then = rule["then"] # get the "then" portion (consequent) for the rule

        # grab the rule's sequence positional information
        # will apply this to each item in the "then" portion to pass forward
        seq_start = None 
        seq_end = None 
        if ("#seq-start" in rule): seq_start = rule["#seq-start"]
        if ("#seq-end" in rule): seq_end = rule["#seq-end"]

        # apply unification variables 
        # (substitute variables from the "when" portion of the rule)
        # then = thoughts.unification.apply_unification(then, unification)
        then = self._apply_values(then, unification)
        # then = self.context.apply(then, unification)

        # add each item in the "then" portion to the agenda
        new_items = []
        if (type(then) is list): new_items = then
        else: new_items.append(then)
        # i = 0
        for item in new_items:
            
            # resolve as many $items as possible
            # (this will happen again during assertion)
            # revise - item = self._resolve_items(item)
            # item = self._resolve_items(item)
            
            if (seq_start is not None) and (type(item) is dict): 
                item["#seq-start"] = seq_start

            if (seq_end is not None) and (type(item) is dict): 
                item["#seq-end"] = seq_end

            self.log_message("ADD:\t\t" + str(item) + " to the agenda")
            # self._agenda.insert(i, item)
            # i = i + 1
            result.append(item)
        
        return result

    def _apply_values(self, term, provider):
        
        if (type(term) is dict):
            result = {}
            for key in term.keys():
                if key == "#into" or key == "#append" or key == "#push":
                    result[key] = term[key]
                elif (key == "#combine"):
                    items_to_combine = term["#combine"]
                    newval = {}
                    for item in items_to_combine:
                        new_item = self._apply_values(item, provider)
                        newval = {**new_item, **newval}
                    # assume combine is a standalone operation
                    # could also merge this will other keys
                    # result[key] = newval
                    return newval
                else:
                    newval = self._apply_values(term[key], provider)
                    result[key] = newval
            return result

        elif (type(term) is list):
            result = []
            for item in term:
                newitem = self._apply_values(item, provider)
                result.append(newitem)
            return result

        elif (type(term) is str):
            if type(provider) is dict:
                term = thoughts.unification.retrieve(term, provider)
            else:
                term = self.context.retrieve(term)
            return term

        else:
            return term

    def _attempt_rule(self, rule, assertion):

        if "when" not in rule: return # if the item is not a rule then skip it
        result = [] 
        when = rule["when"] # get the "when" portion of the rule
        # self.log_message("EVAL:\t" + str(assertion) + " AGAINST " + str(rule))

        # if the "when" portion is a list (sequence)
        if (type(when) is list):

            # arcs - test if arc position matches assertion's position
            # (ignore if no positional information)
            assertion_start = 0
            assertion_end = 0
            rule_start = None
            rule_end = None
            if ("#seq-start" in assertion): assertion_start = assertion["#seq-start"]        
            if ("#seq-end" in assertion): assertion_end = assertion["#seq-end"]
            if ("#seq-start" in rule): rule_start = rule["#seq-start"]   
            if ("#seq-end" in rule): rule_end = rule["#seq-end"]

            if (rule_end is not None): 
                if (assertion_start != rule_end): return

            # find the current constituent
            if ("#seq-idx" not in rule): rule["#seq-idx"] = 0
            seq_idx = rule["#seq-idx"]      
            candidate = when[seq_idx]
            
            # attempt unification (sequences)
            unification = thoughts.unification.unify(assertion, candidate)
            
            if unification is None: return None

            # next constituent in sequence unified
            unification["?#when"] = copy.deepcopy(assertion)

            # the constituent matched, extend the arc
            # self.log_message("MATCHED:\t" + str(assertion) + " AGAINST " + str(rule))

            # clone the rule
            cloned_rule = copy.deepcopy(rule)

            # move to the next constituent in the arc                
            seq_idx = seq_idx + 1
            cloned_rule["#seq-idx"] = seq_idx

            # update the position information for the arc
            if rule_start is None: cloned_rule["#seq-start"] = assertion_start
            cloned_rule["#seq-end"] = assertion_end

            # merge unifications (variables found)
            if ("#unification" not in cloned_rule): 
                cloned_rule["#unification"] = unification
            else:
                current_unification = cloned_rule["#unification"]
                cloned_rule["#unification"] = {**current_unification, **unification}

            # check if arc completed
            if (seq_idx == len(when)): # arc completed           
                unification = cloned_rule["#unification"]
                self.log_message("ARC-COMPLETE:\t" + str(cloned_rule))
                sub_result = self._process_then(cloned_rule, unification)
                self._merge_into_list(result, sub_result)

            else: # arc did not complete - add to active arcs          
                self.log_message("ARC-EXTEND:\t" + str(cloned_rule))
                self._arcs.append(cloned_rule)

        # else "when" part is not a non-sequential structure
        else:

            # when = self._resolve_items(when)
            unification = thoughts.unification.unify(assertion, when)

            if unification is None: return None

            unification["?#when"] = copy.deepcopy(assertion)
            cloned_rule = copy.deepcopy(rule)
            self.log_message("MATCHED:\t" + str(cloned_rule))
            sub_result = self._process_then(cloned_rule, unification)
            self._merge_into_list(result, sub_result)

        return result

    def clear_arcs(self):
        self._arcs = []

    def _attempt_arcs(self, assertion):
        # run the agenda item against all arcs
        result = []
        for rule in self._arcs:           
           sub_result = self._attempt_rule(rule, assertion)
           result = self._merge_into_list(result, sub_result)
        return result

    def _attempt_rules(self, assertion):
        # run the agenda item against all items in the context
        result = []
        for ruleset in self.context.rulesets:
            for rule in ruleset["rules"]:
                sub_result = self._attempt_rule(rule, assertion)
                result = self._merge_into_list(result, sub_result)
        return result

    def _parse_command_name(self, assertion):

        # grab the first where key starts with hashtag (pound)
        for key in assertion.keys(): 
            if key == "#append": continue
            if key == "#into": continue
            if key == "#push": continue
            # if key == "#replace": continue
            if key == "#unification": continue
            if key.startswith("#"): return key 

    def clear_context_items(self):
        self.context.clear_items()

    def process_assertion(self, assertion):
        
        result = []

        assertions = None
        if type(assertion) is not list: assertions = [assertion]
        else: assertions = assertion

        for assertion in assertions: 

            self.log_message("")
            self.log_message("ASSERT:\t\t" + str(assertion))

            # substitute $ items
            # assertion = thoughts.unification.apply_unification(assertion, self.context.items)
            # assertion = self._resolve_items(assertion)
            assertion = self._apply_values(assertion, self.context)

            if (type(assertion) is dict):   
                    
                command = self._parse_command_name(assertion)

                if command is not None:
                    if (command == '#clear-arcs'): 
                        self.clear_arcs()
                        return None
                    elif command == "#assert":
                        assertion = assertion["#assert"]
                    else:
                        sub_result = self._call_plugin(command, assertion)
                        result = self._merge_into_list(result, sub_result)
                        return result # do not run rules?

            sub_result = self._attempt_arcs(assertion)
            result = self._merge_into_list(result, sub_result)
            sub_result = self._attempt_rules(assertion)
            result = self._merge_into_list(result, sub_result)
        
        return result
        
    def _merge_into_list(self, main_list: list, item):
        if item is None: return main_list
        if main_list is None: main_list = []     
        if type(item) is list:
            for sub_item in item: main_list.append(sub_item)
        else:
            main_list.append(item)
        return main_list
            
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
            for item in sub_result:
                self._agenda.append(item)

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

 
