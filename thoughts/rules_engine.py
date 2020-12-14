import json
import os
from thoughts.context import Context
import thoughts.unification
import copy

class RulesEngine:

    context = Context()
    log = []
    _agenda = []
    _plugins = {}
    _arcs = []

    def __init__(self):
        self._load_plugins()

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

    def _call_plugin(self, moniker, assertion):

        if moniker in self._plugins:
            plugin = self._plugins[moniker]
            new_items = plugin.process(assertion, self.context)
            if new_items is not None: 
                if (type(new_items) is list):
                    if len(new_items) > 0: self._agenda.append(new_items)
            return True
        return False

    def log_message(self, message):
        self.log.append(message)

    # load rules from a .json file
    def load_rules(self, file):
        
        if (file.startswith("\\")):
            dir = os.path.dirname(__file__)
            file = dir + file

        with open(file) as f:
            file_rules = list(json.load(f))
            self.context.rules = file_rules
            self.log_message("loaded " + str(len(file_rules)) + " rules from " + file)

    # add a new rule manually
    def add_rule(self, rule):
        self.context.rules.append(rule)

    # process the 'then' portion of the rule
    def _process_then(self, then, unification):
        
        then = thoughts.unification.apply_unification(then, unification)
        
        # run the action, asserting if no specific action indicated
        # print("ASSERT: ", then)
        self.log_message("adding " + str(then) + " to the agenda")
        self._agenda.append(then)
        
    def _attempt_complete(self, rule, assertion):

        when = rule["when"]

        if (type(when) is list):

            # find the current constituent
            if ("#seq-pos" not in rule): rule["#seq-pos"] = 0
            pos = rule["#seq-pos"]
            
            candidate = when[pos]
            
            # attempt unification
            unification = thoughts.unification.unify(candidate, assertion)          
            if (unification is not None):
                
                # clone the rule
                cloned_rule = copy.deepcopy(rule)
                
                # constituent matched, extend the arc
                pos = pos + 1
                cloned_rule["#seq-pos"] = pos

                # merge unifications
                if ("#unification" not in cloned_rule): 
                    cloned_rule["#unification"] = unification
                else:
                    current_unification = cloned_rule["#unification"]
                    cloned_rule["#unification"] = {**current_unification, **unification}

                # check if arc completed
                if (pos == len(when)):
                    # arc completed
                    return cloned_rule["#unification"]
                else:
                    # arc did not complete - add to active arcs
                    self._arcs.append(cloned_rule)
                    pass

        else:
            unification = thoughts.unification.unify(when, assertion)
            return unification

        return None

    def _attempt_rule(self, rule, assertion):

         # if the item is not a rule then skip it
        if "when" not in rule: return None
        
        # try completing the rule         
        unification = self._attempt_complete(rule, assertion)
        
        # if the unification succeeded
        if (unification is not None):
            self._process_then(rule["then"], unification)

    def clear_arcs(self):
        self._arcs = []

    def _attempt_arcs(self, assertion):
        
        # run the agenda item against all arcs
        for rule in self._arcs:           
           self._attempt_rule(rule, assertion)

    def _attempt_rules(self, assertion):

        # run the agenda item against all items in the context
        for rule in self.context.rules:
            self._attempt_rule(rule, assertion)

    def _resolve_items(self, term):

        if (type(term) is dict):
            result = {}
            for key in term.keys():
                newval = self._resolve_items(term[key])
                result[key] = newval
            return result

        elif (type(term) is list):
            result = []
            for item in term:
                newitem = self._resolve_items(item)
                result.append(newitem)
            return result

        elif (type(term) is str):
            term = self.context.find_item(term)
            return term

        else:
            return term

    def _parse_command_name(self, assertion):

        # grab the first where key starts with hashtag (pound)
        for key in assertion.keys(): 
            if key.startswith("#"): 
                return key 

    def process_assertion(self, assertion):
        
        # substitute $ items
        assertion = self._resolve_items(assertion)

        if (type(assertion) is dict):   
                  
            command = self._parse_command_name(assertion)

            if command is not None:
                if (command == '#clear-arcs'): 
                    self.clear_arcs()
                    return
                else:
                    result = self._call_plugin(command, assertion)
                    if result == True : return

        self._attempt_arcs(assertion)
        self._attempt_rules(assertion)
        
    # run the assertion - match and fire rules
    def run_assert(self, assertion):

        # parse json-style string assertion into dict
        if (type(assertion) is str):
            if (assertion.startswith("{")):
                assertion = json.loads(assertion)

        # add assertion to the agenda
        self._agenda.append(assertion)

        # while the agenda has items
        while(len(self._agenda) > 0):

            # grab the topmost agenda item
            current_assertion = self._agenda.pop(0)
            self.log_message("asserting " + str(current_assertion))

            # process it
            if (type(current_assertion) is list): 
                for sub_assertion in current_assertion:  
                    self.process_assertion(sub_assertion)
            else: 
                self.process_assertion(current_assertion)
                    
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
