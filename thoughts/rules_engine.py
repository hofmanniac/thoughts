import json
import os
from thoughts.context import Context
import thoughts.unification

class RulesEngine:

    context = Context()
    log = []
    _agenda = []
    _plugins = {}

    def __init__(self):
        self._load_plugins()

    def load_plugin(self, moniker, dotpath):
        plugin_module = __import__(dotpath, fromlist=[''])
        self._plugins[moniker]  = plugin_module

    def _load_plugins(self):
        self.load_plugin("#output", "thoughts.commands.output")
        self.load_plugin("#prompt", "thoughts.commands.prompt") 
        self.load_plugin("#read-rss", "thoughts.commands.read_rss")    

    def _call_plugin(self, moniker, assertion):
        if moniker in self._plugins:
            plugin = self._plugins[moniker]
            plugin.process(assertion, self.context)
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

    def _apply_unification(self, term, unification):
        
        if (type(term) is dict):
            result = {}
            for key in term.keys():
                newval = self._apply_unification(term[key], unification)
                result[key] = newval
            return result

        elif (type(term) is list):
            result = []
            for item in term:
                newitem = self._apply_unification(item, unification)
                result.append(newitem)
            return result

        elif (type(term) is str):
            # substitute unification into the then part
            for key in unification.keys(): 
                term = term.replace(key, unification[key])
            # term = self.context.find_item(term)
            return term

        else:
            return term

    # process the 'then' portion of the rule
    def _process_then(self, then, unification):
        
        then = self._apply_unification(then, unification)
        
        # run the action, asserting if no specific action indicated
        # print("ASSERT: ", then)
        self.log_message("adding " + str(then) + " to the agenda")
        self._agenda.append(then)
        
    def search_rules(self, assertion):

        # run the agenda item against all items in the context
        for rule in self.context.rules:
            
            # if the item is not a rule then skip it
            if "when" not in rule: continue
            
            # try unifying the when part with the agenda item
            when = rule["when"]
            unification = thoughts.unification.unify(when, assertion)
            
            # if the unification succeeded
            if (unification is not None):
                self._process_then(rule["then"], unification)

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

        return None

    def _parse_command_name(self, assertion):
        # grab the first
            # hashkeys = [value for key,value in assertion.items() if key.startswith("#")]
            # if len(haskeys) > 0: command = hashkeys[0]
            # command = next(iter(assertion))
            command = None
            for key in assertion.keys(): 
                if key.startswith("#"): 
                    return key 

    def process_command(self, assertion):
        
        assertion = self._resolve_items(assertion)

        if (type(assertion) is dict):   
                  
            command = self._parse_command_name(assertion)

            if command is not None:
                result = self._call_plugin(command, assertion)
                if result == True : return

        self.search_rules(assertion)
        
    # run the assertion - match and fire rules
    def run_assert(self, assertion):

        if (type(assertion) is str):
            if (assertion.startswith("{")):
                assertion = json.loads(assertion)

        # add assertion to the agenda
        self._agenda.append(assertion)

        # while the agenda has items
        while(len(self._agenda) > 0):

            # grab the topmost agenda item
            current_assertion = self._agenda.pop()
            self.log_message("asserting " + str(current_assertion))

            # process it
            if (type(current_assertion) is list): 
                for sub_assertion in current_assertion:  
                    self.process_command(sub_assertion)
            else: 
                self.process_command(current_assertion)
                    

