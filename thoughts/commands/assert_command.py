# from pickletools import anyobject
# from typing import Any
from thoughts import context as ctx
import thoughts.unification
import copy

def process(command, context: ctx.RulesContext):
    
    # will collect result conclusions generated
    result = []

    # grab the assertion from the command, else the assertion is the command itself
    assertion = command["#assert"] if "#assert" in command else command

    # if no assertion then done
    if assertion is None: return None

    # if the assertion is a literal - just keep the original command
    # this will preserve the sequence or other meta-information from the assertion
    assertion = command if type(assertion) is not list and type(assertion) is not dict else assertion

    # ensure sequence information is on the assertion
    if "#seq-start" in command and "#seq-start" not in assertion:
        assertion["#seq-start"] = command["#seq-start"]
        assertion["#seq-end"] = command["#seq-end"]

    # search and try to extend arcs
    sub_result = attempt_arcs(assertion, context)
    result = context.merge_into_list(result, sub_result)

    # search and try to trigger rules
    sub_result = attempt_rulesets(assertion, context)
    result = context.merge_into_list(result, sub_result)

    # either store or return the result
    stored = context.store_item(command, result)
    if stored == False: return result

def attempt_arcs(assertion, context: ctx.RulesContext):
   
    # run the agenda item against all arcs
    result = []
    extended_arcs = []
    for idx, arc in enumerate(context.arcs): 
        sub_result = attempt_rule(arc, assertion, context)
        result = context.merge_into_list(result, sub_result)

        # end non-sequential assertions after one match
        # to prevent two matches returned in A B C -> MATCH for A B D A B C
        if "#seq-start" not in assertion and sub_result is not None:
            extended_arcs.append(arc)

    for arc in extended_arcs:
        context.arcs.remove(arc)

    # # remove arcs marked for removal (completed, non-positionally aware)
    # for arc in context.arcs:
    #     if "#remove-me" in arc:
    #         context.arcs.remove(arc)

    return result

def attempt_rulesets(assertion, context: ctx.RulesContext):
    # run the agenda item against all rulesets in the context
    result = []

    candidates = context.search_index(assertion)
    if candidates is not None:
        sub_result = attempt_rules(assertion, candidates, context)
        result = context.merge_into_list(result, sub_result)
    
    else:
    #if len(result) == 0:
        for ruleset in context.rulesets:
            rules = ruleset["rules"]
            sub_result = attempt_rules(assertion, rules, context)
            result = context.merge_into_list(result, sub_result)
            
    return result

def attempt_rules(assertion, rules:list, context:ctx.RulesContext):
    # run the agenda item against all items in the ruleset
    result = []
    for item in rules:
        if "#if" in item: 
            sub_result = attempt_if(item, assertion, context)
            if type(sub_result) is bool: sub_result = None
        else: sub_result = attempt_rule(item, assertion, context)
        result = context.merge_into_list(result, sub_result)
    return result

def attempt_if(item, assertion, context: ctx.RulesContext):
    
    if_portion = None
    if "#if" in item: if_portion = item["#if"]
    elif "if" in item: if_portion = item["if"]
    if if_portion == None: return True

    result = False

    if type(if_portion) is str:
        compare_name = item["equals"]
        condition = {"value": if_portion, "equals": compare_name}
        result = attempt_condition(condition, context)

    elif type(if_portion) is list:
        list_result = True
        for condition in if_portion:
            sub_result = attempt_condition(condition, context)
            if sub_result == False:
                list_result = False
                break
        result = list_result

    elif type(if_portion is dict):     
        result = attempt_condition(if_portion, context)

    if result == True:
        if "#then" in item:
            rules = item["#then"]
            result = attempt_rules(assertion, rules, context)
            return result

    return result

def attempt_condition(condition:dict, context: ctx.RulesContext):
    
    result = False

    x_name = condition["value"]
    y_name = condition["equals"]

    x_val = context.retrieve(x_name)
    y_val = context.retrieve(y_name)

    if (x_val == y_val): result = True

    return result

def attempt_rule(rule, assertion, context: ctx.RulesContext):

    if "#when" not in rule: return # if the item is not a rule then skip it
    result = [] 
    when = rule["#when"] # get the "when" portion of the rule
    # self.log_message("EVAL:\t" + str(assertion) + " AGAINST " + str(rule))

    # if the "#when" portion is a list (sequence)
    if (type(when) is list):

        # gather sequence information
        assertion_start = assertion["#seq-start"] if "#seq-start" in assertion else None       
        assertion_end = assertion["#seq-end"] if "#seq-end" in assertion else None
        # if ("#seq-start" in rule): rule_start = rule["#seq-start"]   
        rule_end = rule["#seq-end"] if "#seq-end" in rule else None 
        seq_idx = rule["#seq-idx"] if "#seq-idx" in rule else 0
        seq_type = rule["#seq-type"] if "#seq-type" in rule else None

        # arcs - test if arc position matches assertion's position
        # (ignore if no positional information)
        if rule_end is not None:    
            if seq_type == "overlap-connected":
                if assertion_start + 1 != rule_end: return
            elif seq_type == "allow-junk":
                if assertion_start + 1 <= rule_end: return
            elif seq_type == "set":
                pass #sets do not use position
            else:
                if assertion_start != rule_end: return

        assertion_term = assertion["#assert"] if "#assert" in assertion else assertion
        # unification = None

        if seq_type == "set":

            def extract_constituents(items: list):
                result = []
                for item in items:
                    if "#seq" in item:
                        sub_items = extract_constituents(item["#seq"])
                        result.extend(sub_items)
                    seq_start = item["#seq-start"] if "#seq-start" in item else None
                    seq_end = item["#seq-end"] if "#seq-end" in item else None
                    if seq_start is not None or seq_end is not None:
                        result.append({"#seq-start": seq_start, "#seq-end": seq_end})
                return result

            def constituent_exists(assertion, when):
                assertion_constituents = extract_constituents([assertion])
                rule_constituents = extract_constituents(when)
                if len(assertion_constituents) == 0 or len(rule_constituents) == 0:
                    return False
                for item1 in assertion_constituents:
                    for item2 in rule_constituents:
                        if item1["#seq-start"] == item2["#seq-start"] and item1["#seq-end"] == item2["#seq-end"]:
                            return True
                return False

            seq_allow_multi = rule["#seq-allow-multi"] if "#seq-allow-multi" in rule else False
            if seq_allow_multi == False:
                # check if this assertion is in any other consituent in the arc
                exists = constituent_exists(assertion, when)
                if exists == True:
                    return

            # for constituent in when:
            #     con_start = constituent["#seq-start"] if "#seq-start" in constituent else None
            #     con_end = constituent["#seq-end"] if "#seq-start" in constituent else None
            #     if con_start == assertion_start and con_end == assertion_end:
            #         # found in previous
            #         return

            # find the first constituent not already matched that unifies, regardless of order
            for pat_idx, pattern_term in enumerate(when):
                if "#seq-start" in pattern_term: continue # consituent already matched
                if "#unification" in rule:
                    pattern_term = context.apply_values(pattern_term, rule["#unification"])     
                unification = thoughts.unification.unify(assertion_term, pattern_term)
                if unification is not None: 
                    seq_idx = pat_idx
                    break

        else:

            # test if this assertion is already in another previous part of the sequence
            # todo - make this recursive
            # todo - factor in overlap-connection option
            for con_idx, constituent in enumerate(when):
                if con_idx >= seq_idx: break
                con_start = constituent["#seq-start"] if "#seq-start" in constituent else None
                con_end = constituent["#seq-end"] if "#seq-start" in constituent else None
                if con_start == assertion_start and con_end == assertion_end:
                    # found in previous
                    return

            # compare the current consituent
            pattern_term = when[seq_idx]
            if "#unification" in rule:
                pattern_term = context.apply_values(pattern_term, rule["#unification"])
            unification = thoughts.unification.unify(assertion_term, pattern_term)
        
        # next constituent in sequence unified
        if unification is None: return None
        # self.log_message("MATCHED:\t" + str(assertion) + " AGAINST " + str(rule))
        unification["?#when"] = copy.deepcopy(assertion)       
        cloned_rule = copy.deepcopy(rule) # clone the rule

        # replace consituent with the one that matched
        # cloned_rule["#when"][seq_idx] = assertion_term
        cloned_rule["#when"][seq_idx] = assertion

        if seq_type != "set":  
            # move to the next constituent in the arc
            seq_idx += 1
            cloned_rule["#seq-idx"] = seq_idx

        # update the position information for the arc
        rule_start = cloned_rule["#seq-start"] if "#seq-start" in cloned_rule else None
        if rule_start is None: 
            cloned_rule["#seq-start"] = assertion_start
        else:
            cloned_rule["#seq-start"] = rule_start
        cloned_rule["#seq-end"] = assertion_end

        # merge unifications (variables found)
        if ("#unification" not in cloned_rule): 
            cloned_rule["#unification"] = unification
        else:
            current_unification = cloned_rule["#unification"]
            cloned_rule["#unification"] = {**current_unification, **unification}

        # check if arc completed
        # improve - could probably just keep the first check, they do the same thing
        arc_completed = True
        if seq_type == "set": # check if all constituents have been found
            for constituent in cloned_rule["#when"]:
                if "#seq-start" not in constituent:
                    arc_completed = False
                    break
        elif seq_idx < len(when): # check if at the end of the sequence
            arc_completed = False

        if arc_completed: # arc completed           
            unification = cloned_rule["#unification"]
            context.log_message("ARC-COMPLETE:\t" + str(cloned_rule))
            sub_results = process_then(cloned_rule, unification, context)

            # add structure information into sub_result
            for sub_result in sub_results:
                sub_result["#seq"] = cloned_rule["#when"]

            context.merge_into_list(result, sub_results)

        else: # arc did not complete - add to active arcs          
            context.log_message("ARC-EXTEND:\t" + str(cloned_rule))
            cloned_rule["#is-arc"] = True
            context.arcs.append(cloned_rule)

        # # if this is a non-positionally aware assertion
        # # then signal to remove the arc - a new arc will take its place
        # if "#seq-start" not in assertion and "#is-arc" in rule:
        #     rule["#remove-me"] = True

    # else "when" part is not a non-sequential structure
    else:

        pattern_term = context.apply_values(when, context)
        assertion_term = assertion["#assert"] if "#assert" in assertion else assertion

        unification = thoughts.unification.unify(assertion_term, pattern_term)
        if unification is None: return None

        truth = attempt_if(rule, assertion_term, context)

        if truth == True:
            unification["?#when"] = copy.deepcopy(assertion_term)
            cloned_rule = copy.deepcopy(rule)
            context.log_message("MATCHED:\t" + str(cloned_rule))
            sub_results = process_then(cloned_rule, unification, context)

            # add structure information into sub_result
            # for sub_result in sub_results:
            #     sub_result["#seq"] = cloned_rule["#when"]

            context.merge_into_list(result, sub_results)

    return result

   # process the 'then' portion of the rule
def process_then(rule, unification, context: ctx.RulesContext):
    
    result = []
    then = rule["#then"] # get the "then" portion (consequent) for the rule

    # grab the rule's sequence positional information
    # will apply this to each item in the "then" portion to pass forward
    seq_start = None 
    seq_end = None 
    if ("#seq-start" in rule): seq_start = rule["#seq-start"]
    if ("#seq-end" in rule): seq_end = rule["#seq-end"]

    # apply unification variables 
    # (substitute variables from the "when" portion of the rule)
    # then = thoughts.unification.apply_unification(then, unification)
    then = context.apply_values(then, unification)
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
        
        new_item = copy.deepcopy(item)

        if type(new_item) is not dict and type(new_item) is not list:
            new_item = {"#assert": new_item}

        if (seq_start is not None) and (type(new_item) is dict): 
            new_item["#seq-start"] = seq_start

        if (seq_end is not None) and (type(new_item) is dict): 
            new_item["#seq-end"] = seq_end

        context.log_message("ADD:\t\t" + str(new_item) + " to the agenda")
        # self._agenda.insert(i, item)
        # i = i + 1
        result.append(new_item)
    
    return result