import thoughts.unification as unification
import uuid

class Context:

    default_ruleset = None
    rulesets = []
    items = {}

    def add_ruleset(self, rules: list, name: str = None, path: str = None):
        if name is None: name = str(uuid.uuid4())
        ruleset = {"name": name, "rules": rules, "path": path}
        self.rulesets.append(ruleset)

    def clear_items(self):
        for key in self.items.keys():
            if str.startswith(key, "$"): continue 
            self.items.pop(key)
        # self.items = {}

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

    def _find_in_item(self, part, currentItem):
        
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

                    current_item = self._find_in_item(part_name, current_item)

                    if part_idx is not None:
                        if type(current_item) is list:
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

                if token in self.items: result = result + " " + str(self.items[token])
                else: result = result + " " + token

            else:

                result = result + " " + token
                continue    

        return result.strip()
