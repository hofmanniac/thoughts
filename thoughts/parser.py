
from thoughts.operations.rules import Equals, HasValue, LastMessage, Unifies

class ConfigParser():
    def parse_logic_condition(config: dict):
        if config is None:
            return None
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