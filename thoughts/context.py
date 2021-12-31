import thoughts.unification as unification
import uuid
from time import time

class Context:

    default_ruleset = None
    rulesets = []
    items = {}
    arcs = []
    log = []
    display_log = False
    last_ms = 0
    index = {}

    def __init__(self):
        self.default_ruleset = None
        self.rulesets = []
        self.items = {}
        self.arcs = []
        self.log = []
        self.display_log = False
        self.last_ms = 0
        self.index = {}

    def print_items(self):
        print("==================================")
        for key in self.items.keys():
            print(key + ":", self.items[key])
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

    def update_index(self, term):
        
        if "when" not in term: return

        when_part = term["when"]
        if type(when_part) is str:
            tokens = unification.tokenize(when_part)
            for token in tokens:
                if str.startswith(token, "?") or str.startswith(token, "$"): continue
                self.append_dict(self.index, token, term)
        elif type(when_part) is dict:
            if "#no-match" in when_part:
                self.append_dict(self.index, "#no-match", term)

    def search_index(self, term):
        result = []
        if type(term) is str:
            tokens = unification.tokenize(term)
            for token in tokens:
                if token not in self.index: continue
                items = self.index[token]
                if items is not None:
                    if type(items) is list:
                        for item in items:
                            if item not in result: result.append(item)
                    elif items not in result: result.append(items)
        elif type(term) is dict:
            for key in term.keys():
                if key == "#no-match": 
                    items = self.search_index(key)
                else: 
                    items = self.search_index(term[key])
                if items is not None: 
                    for item in items:
                        if item not in result: result.append(item)

        if len(result) == 0: return None
        else: return result

    def index_rules(self, rules:list):
        for rule in rules: self.update_index(rule)

    def append_dict(self, d:dict, key:str, term):
        if key in d.keys(): 
            current_val = d[key]
            if (current_val is None): d[key] = term
            else:
                if type(current_val) is list:
                    if term not in current_val: # uses is or ==?
                        current_val.append(term)
                else:
                    if type(current_val) is str and type(term) is str and current_val != term:
                        d[key] = [current_val, term]
                    elif current_val is not term:
                        d[key] = [current_val, term]
        else: d[key] = term

    def log_message(self, message):
        if self.display_log == True:
            if len(message) > 0:
                milliseconds = int(time() * 1000)
                diff = milliseconds - self.last_ms
                if self.last_ms == 0: diff = 0
                self.last_ms = milliseconds
                print(">", "[" + str(diff) + "ms]\t", message)
        self.log.append(message)

    def merge_into_list(self, main_list: list, item):
        if item is None: return main_list
        if main_list is None: main_list = []     
        if type(item) is list:
            for sub_item in item: main_list.append(sub_item)
        else: main_list.append(item)
        return main_list

    def _add_rules(self, rules: list, name: str = None, path: str = None):

        if name is None: name = str(uuid.uuid4())

        ruleset = next(filter(lambda rs: rs["name"] == name, self.rulesets), None)

        if ruleset is None:

            ruleset = {"name": name, "rules": rules, "path": path}

            # sorted_set = []
            # added = False
            # for item in self.rulesets:
            #     if len(rules) < len(item["rules"]):
            #         added = True
            #         sorted_set.append(ruleset)
            #     sorted_set.append(item)
            # if added == False: sorted_set.append(ruleset)
            # self.rulesets = sorted_set

            self.rulesets.append(ruleset)

            self.index_rules(rules)

    def add_rule(self, rule):
        self.default_ruleset["rules"].append(rule)
        self.update_index(rule)

    def clear_variables(self):
        for key in self.items.keys():
            if str.startswith(key, "$"): continue 
            self.items.pop(key)

    def store_item(self, assertion, item):

        if type(item) is list and len(item) == 1: item = item[0]
        
        if ("#into" in assertion):
            var_name = assertion["#into"]
            self.items[var_name] = item
            # if str.startswith(var_name, "$"):
            #     var_name = var_name[1:]
            #     if type(item) is str:
            #         item = {"#item": var_name, "#": item}
            #     else:
            #         pass
            #     self.default_ruleset["rules"].append(item)
            # else:
            #     self.items[var_name] = item
            return True

        elif ("#append" in assertion):
            var_name = assertion["#append"]
            if var_name in self.items: 
                current_val = self.items[var_name]
                if (current_val is None):
                    self.items[var_name] = item
                else:
                    if type(current_val) is list: 
                        current_val.append(item)
                    else:
                        self.items[var_name] = [current_val, item]
                return True
            else:
                self.items[var_name] = item
                return True

        elif ("#push" in assertion):
            var_name = assertion["#push"]
            if var_name in self.items: 
                current_val = self.items[var_name]
                if (current_val is None):
                    self.items[var_name] = item
                else:
                    if type(current_val) is list: 
                        current_val.insert(0, item)
                    else:
                        self.items[var_name] = [item, current_val]
                return True
            else:
                self.items[var_name] = item
                return True

        return False

    def _find_items(self, query, stopAfterFirst):
        
        results = []

        if "#item" in query:
            itemname = query["#item"]
            if itemname in self.items:
                search = self.items[itemname]
                if (search is not None):
                    results.append(search)
                    if (stopAfterFirst): return results

        for ruleset in self.rulesets:

            for source in ruleset["rules"]:
            
                if "#item" not in source: continue
                if (source is None): continue

                u = unification.unify(source, query)
                if (u is None): continue
                
                source["#unification"] = u
                results.append(source)

                if (stopAfterFirst): return results[0]
            
        return results

    def _find_items_by_name(self, item):
        query = {}
        query["#item"] = item
        return self._find_items(query, False)

    def _find_in_item(self, currentItem, part):
        
        if (part.startswith("$")):

            # token = part[1:]
            currentItem = self._find_items_by_name(part)
            if len(currentItem) == 0: currentItem = part
            
        else:
        
            if (type(currentItem) is str):
                currentItem = self._find_items_by_name(str(currentItem))
            
            if (type(currentItem) is dict):
            
                joCurrentItem = currentItem
                if (joCurrentItem[part] is not None):    
                    currentItem = joCurrentItem[part]
            
            elif (type(currentItem) is list):
                resultlist = []
                for jtItem in currentItem:            
                    if (type(jtItem) is dict):
                        joItem = jtItem
                        if (joItem[part] is not None):
                            currentItem = joItem[part]
                            resultlist.append(currentItem)
                    # some other kind of custom class / object - try a dictionary-type resolution
                    # this will break if that object does not support dictionary indexing
                    else: 
                        joItem = jtItem
                        if (joItem[part] is not None):
                            currentItem = joItem[part]
                            resultlist.append(currentItem)
                currentItem = resultlist

        result = currentItem

        if (currentItem != None and type(currentItem) == list):
        
            jaCurrentItem = currentItem
            if (len(jaCurrentItem) == 1): result = jaCurrentItem[0]
        
        if result is None:
            result = part

        return result

    def retrieve(self, text):

        if ("$" not in text) and ("?" not in text): return text

        results = []

        # tokens = text.split(' ')
        tokens = unification.tokenize(text)

        for token in tokens:

            if str.startswith(token, "?") or str.startswith(token, "$"):

                parts = token.split('.')
                current_item = None

                for part in parts:
                    if current_item is None: # first portion
                        current_item = self.retrieve_items(part)
                    else:
                        if type(current_item) is dict:
                            if part in current_item: 
                                current_item = current_item[part]
                            else:
                                break
                        else:
                            break # later - determine how to handle lists and other types

                    if current_item is None:
                        current_item = token
                        break 

                results.append(current_item)
            else:

                results.append(token) 

        if len(results) == 0: return None
        if len(results) == 1: return results[0]
        else:
            text = ""
            for result in results: 
                if result == "?" or result == ".":
                    text = text + str(result)
                else:
                    text = text + " " + str(result)
            text = text.strip()
            return text

    def retrieve_items(self, item_name, stop_after_first = False):
        
        results = []

        if item_name in self.items: 
            results.append(self.items[item_name])
            if (stop_after_first): return results[0]

        for ruleset in self.rulesets:

            for item in ruleset["rules"]:

                if (item is None): continue            
                if "#item" not in item: continue

                if "$" + item["#item"] == item_name \
                    or item["#item"] == item_name or "?" + item["#item"] == item_name:
                    results.append(item)
                    if (stop_after_first): return results[0]
        
        if len(results) == 0: return None
        if len(results) == 1: return results[0]
        else: return results

    def retrieve2(self, text):

        if ("$" not in text) and ("?" not in text): return text

        tokens = text.split(' ')
        result = ""

        for token in tokens:

            if (token.startswith("$")):

                parts = token.split('.')
                current_item = None

                for part in parts:

                    if len(part) == 0: 
                        part = "#"

                    part_idx = None
                    idx_bracket_start = str.find(part, "[")
                    if idx_bracket_start > -1:
                        part_name = part[:idx_bracket_start]
                        idx_bracket_end = str.find(part, "]")
                        part_idx = part[idx_bracket_start + 1: idx_bracket_end]
                    else:
                        part_name = part

                    current_item = self._find_in_item(current_item, part_name)

                    if part_idx is not None:
                        if type(current_item) is list:
                            part_idx = int(part_idx)
                            current_item = current_item[part_idx]

                if (type(current_item) is str):
                    result = result + " " + current_item

                elif (type(current_item) is list):
                    for item in current_item:
                        result = result + " " + str(item)
                else:
                    if len(result) > 0:
                        result = result + str(current_item)
                        return result
                    else:
                        return current_item

            elif token.startswith("?"):

                if token in self.items:
                    if type(self.items[token] is list):
                        for item in self.items[token]:
                            # refactor - this needs to be recursive
                            result = result + " " + str(item) 
                    else:
                        result = result + " " + str(self.items[token])
                else: result = result + " " + token

            else:

                result = result + " " + token
                continue    

        return result.strip()

    def apply_values(self, term, provider):
            
        if (type(term) is dict):
            result = {}
            for key in term.keys():
                if key == "#into" or key == "#append" or key == "#push":
                    if type(term[key] is str):
                        if type(provider) is dict:
                            sub_value = unification.retrieve(term[key], provider)
                            if sub_value is not None:
                                result[key] = sub_value
                    if key not in result:
                        result[key] = term[key]
                elif (key == "#combine"):
                    items_to_combine = term["#combine"]
                    newval = {}
                    for item in items_to_combine:
                        new_item = self.apply_values(item, provider)
                        newval = {**new_item, **newval}
                    # assume combine is a standalone operation
                    # could also merge this will other keys
                    # result[key] = newval
                    return newval
                else:
                    newval = self.apply_values(term[key], provider)
                    result[key] = newval
            return result

        elif (type(term) is list):
            result = []
            for item in term:
                # moved from rule engine, refactor
                newitem = self.apply_values(item, provider) 
                result.append(newitem)
            return result

        elif (type(term) is str):
            if type(provider) is dict:
                term = unification.retrieve(term, provider)
            else:
                term = self.retrieve(term)
            return term

        else:
            return term
