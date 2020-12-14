import thoughts.unification as unification

class Context:

    rules = []
    items = {}
    
    def find_items(self, query, stopAfterFirst):
        
        results = []

        if "item" in query:
            itemname = query["item"]
            if itemname in self.items:
                search = self.items[itemname]
                if (search is not None):
                    results.append(search)
                    if (stopAfterFirst): return results

        for source in self.rules:
        
            if "item" not in source: continue

            if (source is None): continue

            # for candidateItem in source:
        
            candidateItem = source
            joItem = candidateItem
            # joItem = candidateItem
            # if (type(candidateItem) is not str): joItem = candidateItem.deepcopy()

            u = unification.unify(joItem, query)
            if (u is None): continue

            joItem["#unification"] = u
            results.append(joItem)

            if (stopAfterFirst): return results[0]
            
        return results

    def find_items_by_name(self, item):

        query = {}
        query["item"] = item
        return self.find_items(query, False)

    def _find_in_item(self, part, currentItem):
        
        if (part.startswith("$")):      
            token = part[1:]
            currentItem = self.find_items_by_name(token)
        
        else:
        
            if (type(currentItem) is str):
                currentItem = self.find_items_by_name(str(currentItem))
            
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

    def find_item(self, text):

        if "$" not in text:
            return text

        else:

            tokens = text.split(' ')
            result = ""

            for token in tokens:

                if (token.startswith("$") == False): 
                    result = result + " " + token
                    continue

                parts = token.split('.')
                currentItem = None

                for part in parts:
                    currentItem = self._find_in_item(part, currentItem)

                if (type(currentItem) is str):
                    result = result + " " + currentItem
                else:
                    return currentItem

            return result.strip()
