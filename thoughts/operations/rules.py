from copy import deepcopy
from thoughts.operations.core import Operation
from thoughts.context import Context
from thoughts.operations.workflow import PipelineExecutor
from typing import List
from thoughts.unification import unify

class Unifies(Operation):
    def __init__(self, condition: dict):
        self.condition = condition
    def execute(self, context: Context, message):
        unification = unify(self.condition, message)
        truth = True if unification is not None else False
        return unification, truth

class LogicRule(Operation):
    def __init__(self, condition: Operation, actions: List[Operation], else_actions: List[Operation], supress_execution: bool = False):
        self.condition = condition
        self.actions = actions
        self.else_actions = else_actions
        self.supress_execution = supress_execution
    def execute(self, context: Context, message):
        result, control = self.condition.execute(context, message)
        actions = []
        if control == True:
            for base_action in self.actions:
                action = context.apply_values(base_action, result)
                actions.append(action)
        else:
            for base_action in self.else_actions:
                action = base_action
                actions.append(action)

        if self.supress_execution:
            return actions, None
        else:
            runner = PipelineExecutor(actions, context=context)
            result, control = runner.execute(context, message)
            # pipeline should only execute once for the actions block, extract first result set
            final_result = result[0] if len(result) == 1 else result
            return final_result, control

class HasValue(Operation):
    def __init__(self, item_key: str):
        self.item_key = item_key
    def execute(self, context: Context, message = None):
        test_value = context.get_item(self.item_key)
        truth = True if test_value is not None else False
        return test_value, truth
    
class FactAsserter(Operation):
    def __init__(self, fact: dict):
        self.fact = fact
        self.condition = None
    def execute(self, context: Context, message):
        return self.fact, None
        
class RulesRunner(Operation):
    
    def __init__(self, rules: list = []):
        self.rules = rules
        self.executor = PipelineExecutor()
    
    def add_rule(self, rule: LogicRule):
        self.rules.append(rule)

    def execute(self, context=None, message=None):
        rule: LogicRule
        for rule in self.rules:
            actions = rule.execute(context, message)
            if actions is None:
                continue
            self.executor.execute(context, actions)

        return None, None
