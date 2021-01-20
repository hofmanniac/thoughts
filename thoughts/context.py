import thoughts.unification as unification
import uuid

class Context:

    default_ruleset = None
    rulesets = []
    items = {}
    arcs = []
    log = []

    def log_message(self, message):
        self.log.append(message)

    def merge_into_list(self, main_list: list, item):
        if item is None: return main_list
        if main_list is None: main_list = []     
        if type(item) is list:
            for sub_item in item: main_list.append(sub_item)
        else:
            main_list.append(item)
        return main_list

    def add_ruleset(self, rules: list, name: str = None, path: str = None):
        if name is None: name = str(uuid.uuid4())
        ruleset = {"name": name, "rules": rules, "path": path}
        self.rulesets.append(ruleset)

    def clear_variables(self):
        for key in self.items.keys():
            if str.startswith(key, "$"): continue 
            self.items.pop(key)

    def store_item(self, assertion, item):

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

        tokens = text.split(' ')

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
            for result in results: text = text + " " + str(result)
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
