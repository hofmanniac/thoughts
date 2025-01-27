
class ConfigParser():

    def parse_operation(operation_config: dict, config: dict):
        from thoughts.operations.console import ConsoleReader, ConsoleWriter
        from thoughts.operations.routing import Choice, LLMRoutingAgent
        from thoughts.operations.thought import Express, Thought
        from thoughts.operations.workflow import PipelineExecutor
        from thoughts.operations.rules import LogicRule, Assertion
        from thoughts.interfaces.web import FetchFeed
        from thoughts.operations.prompting import IncludeHistory
        
        if type(operation_config) is str:
            operation_config = {"Assert": operation_config}
            return Assertion.parse_json(operation_config, config)
        elif "Thought" in operation_config:
            return Thought.parse_json(operation_config, config)
        elif "Choice" in operation_config:
            return Choice.parse_json(operation_config, config)
        elif "LLMRoutingAgent" in operation_config:
            return LLMRoutingAgent.parse_json(operation_config, config)
        elif "Ask" in operation_config or "ConsoleReader" in operation_config:
            return ConsoleReader.parse_json(operation_config, config)
        elif "Write" in operation_config or "ConsoleWriter" in operation_config:
            return ConsoleWriter.parse_json(operation_config, config)
        elif "Express" in operation_config:
            return Express.parse_json(operation_config, config)
        elif "PipelineExecutor" in operation_config or "Task" in operation_config:
            return PipelineExecutor.parse_json(operation_config, config)
        elif "When" in operation_config:
            return LogicRule.parse_json(operation_config, config)
        elif "History" in operation_config:
            return IncludeHistory.parse_json(operation_config, config)
        elif "FetchFeed" in operation_config:         
            return FetchFeed.parse_json(operation_config, config)
        elif "Assert" in operation_config:
            return Assertion.parse_json(operation_config, config)
        else:
            operation_config = {"Assert": operation_config}
            return Assertion.parse_json(operation_config, config)

            # raise ValueError(f"Unknown component in PipelineExecutor: {operation_config}")
            # print(f"Unknown component in PipelineExecutor: {operation_config}")

    def parse_operations(node_config: list, config: dict = None):
        if type(node_config) is not list:
            node_config = [node_config]
        operations = []
        for item in node_config:
            operation = ConfigParser.parse_operation(item, config)
            operations.append(operation)
        return operations
    
    def parse_logic_condition(config: dict):
        from thoughts.operations.rules import Equals, HasValue, LastMessage, Unifies, TextMatchCondition
        if config is None:
            return None
        
        if type(config) is str:
            return TextMatchCondition(config)
        if "Equals" in config:
            item_key = config.get("Equals", None)
            value = config.get("value", None)
            return Equals(item_key, value)
        elif "HasValue" in config:
            item_key = config.get("HasValue", None)
            return HasValue(item_key)
        elif "LastMessage" in config:
            role = config.get("LastMessage", None)
            return LastMessage(role=role)
        elif "Unifies" in config:
            condition = config.get("Unifies", None)
            return Unifies(condition)
        return None