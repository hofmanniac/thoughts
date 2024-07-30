from copy import deepcopy
from thoughts.operations.core import Operation
from thoughts.engine import Context, PipelineExecutor
from typing import List
from thoughts.unification import unify

class LogicCondition:
    def __init__(self, condition: dict):
        self.condition = condition
    def evaluate(self, context: Context, message):
        unification = unify(self.condition, message)
        if unification is not None:
            return True, unification
        return False, unification

class LogicRule(Operation):
    def __init__(self, condition: LogicCondition, actions: List[Operation]):
        self.condition = condition
        self.actions = actions
    def execute(self, context: Context, message):
        unification = self.condition.evaluate(context, message)
        if unification is not None:
            actions = []
            for base_action in self.actions:
                action = context.apply_values(base_action, context)
                actions.append(action)
            return actions, None
        return None, None

class FactAsserter(Operation):
    def __init__(self, fact: dict):
        self.fact = fact
        self.condition = None
    def execute(self, context: Context, message):
        return self.fact, None
        
class RulesRunner(Operation):
    
    def __init__(self):
        self.rules = []
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
