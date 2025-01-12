from copy import deepcopy
from thoughts.interfaces.messaging import PromptMessage
from thoughts.operations.core import Operation
from thoughts.context import Context
from typing import List
from thoughts.parser import ConfigParser
from thoughts.unification import unify
import re

# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from thoughts.operations.workflow import PipelineExecutor

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
        _, truth = self.condition.execute(context, message)
        self.execute_actions(context, truth, message)
    def execute_actions(self, context: Context, truth: bool, message = None):
        actions = []
        if truth:
            for base_action in self.actions:
                action = base_action
                actions.append(action)
        else:
            for base_action in self.else_actions:
                action = base_action
                actions.append(action)
        if self.supress_execution:
            return actions, control
        else:
            from thoughts.operations.workflow import PipelineExecutor
            runner = PipelineExecutor(nodes=actions)
            result, control = runner.execute(context, message)
            # pipeline should only execute once for the actions block, extract first result set
            final_result = result[0] if len(result) == 1 else result
            return final_result, control
    @classmethod
    def parse_json(cls, json_snippet, config):
        condition_config = json_snippet.get("When", None)
        condition = ConfigParser.parse_logic_condition(condition_config)
        actions_config = json_snippet.get("Then", [])
        actions = ConfigParser.parse_operations(actions_config, config)
        else_config = json_snippet.get("Else", [])
        else_actions = ConfigParser.parse_operations(else_config, config)
        supress_execution = json_snippet.get("supressActions", False)
        return cls(condition, actions, else_actions, supress_execution)
        
class Equals(Operation):
    def __init__(self, item_key: str, value):
        self.item_key = item_key
        self.value = value
    def execute(self, context: Context, message = None):
        test_value = context.get_item(self.item_key)
        truth = True if test_value == self.value else False
        return test_value, truth

class HasValue(Operation):
    def __init__(self, item_key: str):
        self.item_key = item_key
    def execute(self, context: Context, message = None):
        test_value = context.get_item(self.item_key)
        truth = True if test_value is not None else False
        return test_value, truth
    
class LastMessage(Operation):
    def __init__(self, role: str):
        self.role = role
    def execute(self, context: Context, message = None):
        last_messages = context.peek_messages(1)
        if last_messages is None or len(last_messages) == 0:
            return None, False
        last_message: PromptMessage = last_messages[0]
        if last_message.speaker == self.role:
            return last_message, True
        return last_message, False
    
class TextMatchCondition(Operation):
    def __init__(self, text: str, case_sensitive: bool = False, use_regex: bool = False):
        self.text = text
        self.case_sensitive = case_sensitive
        self.use_regex = use_regex

    def execute(self, context: Context, message = None):
        test_value = None
        if type(message) is str:
            test_value = message
        elif isinstance(message, PromptMessage):
            test_value = message.content

        comparison_text = self.text
        comparison_value = test_value

        if not self.case_sensitive:
            comparison_text = comparison_text.lower()
            comparison_value = comparison_value.lower()

        if self.use_regex:
            truth = bool(re.search(comparison_text, comparison_value))
        else:
            truth = comparison_text == comparison_value

        return self.text, truth
        
class FactAsserter(Operation):
    def __init__(self, fact: dict):
        self.fact = fact
        self.condition = None
    def execute(self, context: Context, message):
        return self.fact, None
        
class RulesRunner(Operation):
    
    def __init__(self, rules: list = []):

        parsed_rules = []
        for rule in rules:
            if type(rule) is dict:
                rule = LogicRule.parse_json(rule, {})
                parsed_rules.append(rule)
            elif isinstance(rule, LogicRule):    
                parsed_rules.append(rule)
            else:
                raise ValueError("RulesRunner can only accept LogicRule instances or dicts.")
        self.rules = parsed_rules

        from thoughts.operations.workflow import PipelineExecutor
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
    def parse_json(cls, json_snippet, config) -> 'RulesRunner':
        rules_config = json_snippet.get("rules", [])
        rules = ConfigParser.parse_operations(rules_config, config)
        return cls(rules)
