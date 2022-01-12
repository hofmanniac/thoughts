from thoughts import context as ctx
import thoughts.unification
import copy

def process(command, context: ctx.Context):
    
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

def attempt_arcs(assertion, context: ctx.Context):
   
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

def attempt_rulesets(assertion, context: ctx.Context):
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

def attempt_rules(assertion, rules:list, context:ctx.Context):
    # run the agenda item against all items in the ruleset
    result = []
    for item in rules:
        if "#if" in item: 
            sub_result = attempt_if(item, assertion, context)
            if type(sub_result) is bool: sub_result = None
        else: sub_result = attempt_rule(item, assertion, context)
        result = context.merge_into_list(result, sub_result)
    return result

def attempt_if(item, assertion, context: ctx.Context):
    
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

def attempt_condition(condition:dict, context: ctx.Context):
    
    result = False

    x_name = condition["value"]
    y_name = condition["equals"]

    x_val = context.retrieve(x_name)
    y_val = context.retrieve(y_name)

    if (x_val == y_val): result = True

    return result

def attempt_rule(rule, assertion, context: ctx.Context):

    if "#when" not in rule: return # if the item is not a rule then skip it
    result = [] 
    when = rule["#when"] # get the "when" portion of the rule
    # self.log_message("EVAL:\t" + str(assertion) + " AGAINST " + str(rule))

    # if the "#when" portion is a list (sequence)
    if (type(when) is list):

        # gather start and end information
        assertion_start = assertion["#seq-start"] if "#seq-start" in assertion else None       
        assertion_end = assertion["#seq-end"] if "#seq-end" in assertion else None
        # if ("#seq-start" in rule): rule_start = rule["#seq-start"]   
        rule_end = rule["#seq-end"] if "#seq-end" in rule else None 

        # arcs - test if arc position matches assertion's position
        # (ignore if no positional information)
        if rule_end is not None: 
            if assertion_start != rule_end: return

        # find the current constituent
        seq_idx = rule["#seq-idx"] if "#seq-idx" in rule else 0
        pattern_term = when[seq_idx]
        assertion_term = assertion["#assert"] if "#assert" in assertion else assertion

        # attempt unification (sequences)
        unification = thoughts.unification.unify(assertion_term, pattern_term)
        
        if unification is None: return None

        # self.log_message("MATCHED:\t" + str(assertion) + " AGAINST " + str(rule))

        # next constituent in sequence unified
        unification["?#when"] = copy.deepcopy(assertion)        
        
        # clone the rule
        cloned_rule = copy.deepcopy(rule)

        # move to the next constituent in the arc                
        seq_idx += 1
        cloned_rule["#seq-idx"] = seq_idx

        # update the position information for the arc
        #if rule_start is None: cloned_rule["#seq-start"] = assertion_start
        cloned_rule["#seq-start"] = assertion_start
        cloned_rule["#seq-end"] = assertion_end

        # merge unifications (variables found)
        if ("#unification" not in cloned_rule): 
            cloned_rule["#unification"] = unification
        else:
            current_unification = cloned_rule["#unification"]
            cloned_rule["#unification"] = {**current_unification, **unification}

        # check if arc completed
        if seq_idx == len(when): # arc completed           
            unification = cloned_rule["#unification"]
            context.log_message("ARC-COMPLETE:\t" + str(cloned_rule))
            sub_result = process_then(cloned_rule, unification, context)
            context.merge_into_list(result, sub_result)

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

        when = context.apply_values(when, context)
        unification = thoughts.unification.unify(assertion, when)
        if unification is None: return None

        truth = attempt_if(rule, assertion, context)

        if truth == True:
            unification["?#when"] = copy.deepcopy(assertion)
            cloned_rule = copy.deepcopy(rule)
            context.log_message("MATCHED:\t" + str(cloned_rule))
            sub_result = process_then(cloned_rule, unification, context)
            context.merge_into_list(result, sub_result)

    return result

   # process the 'then' portion of the rule
def process_then(rule, unification, context: ctx.Context):
    
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

    if type(then) is str:
        then = {"#assert": then}

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

        context.log_message("ADD:\t\t" + str(item) + " to the agenda")
        # self._agenda.insert(i, item)
        # i = i + 1
        result.append(item)
    
    return result