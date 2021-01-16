from thoughts import context as ctx
import thoughts.unification
import copy

def process(command, context: ctx.Context):
    
    result = []

    if "#assert" in command: command = command["#assert"]

    sub_result = attempt_arcs(command, context)
    result = context.merge_into_list(result, sub_result)
    sub_result = attempt_rules(command, context)
    result = context.merge_into_list(result, sub_result)

    # either store or return the result
    stored = context.store_item(command, result)
    if stored == False: return result

def attempt_arcs(assertion, context: ctx.Context):
    # run the agenda item against all arcs
    result = []
    for rule in context.arcs:           
        sub_result = attempt_rule(rule, assertion, context)
        result = context.merge_into_list(result, sub_result)
    return result

def attempt_rules(assertion, context: ctx.Context):
    # run the agenda item against all items in the context
    result = []
    for ruleset in context.rulesets:
        for rule in ruleset["rules"]:
            sub_result = attempt_rule(rule, assertion, context)
            result = context.merge_into_list(result, sub_result)
    return result

def attempt_rule(rule, assertion, context: ctx.Context):

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
            context.log_message("ARC-COMPLETE:\t" + str(cloned_rule))
            sub_result = process_then(cloned_rule, unification, context)
            context.merge_into_list(result, sub_result)

        else: # arc did not complete - add to active arcs          
            context.log_message("ARC-EXTEND:\t" + str(cloned_rule))
            context.arcs.append(cloned_rule)

    # else "when" part is not a non-sequential structure
    else:

        # when = self._resolve_items(when)
        unification = thoughts.unification.unify(assertion, when)

        if unification is None: return None

        unification["?#when"] = copy.deepcopy(assertion)
        cloned_rule = copy.deepcopy(rule)
        context.log_message("MATCHED:\t" + str(cloned_rule))
        sub_result = process_then(cloned_rule, unification, context)
        context.merge_into_list(result, sub_result)

    return result

   # process the 'then' portion of the rule
def process_then(rule, unification, context: ctx.Context):
    
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
        
        if (seq_start is not None) and (type(item) is dict): 
            item["#seq-start"] = seq_start

        if (seq_end is not None) and (type(item) is dict): 
            item["#seq-end"] = seq_end

        context.log_message("ADD:\t\t" + str(item) + " to the agenda")
        # self._agenda.insert(i, item)
        # i = i + 1
        result.append(item)
    
    return result