from thoughts.context import Context
from thoughts.interfaces.messaging import SystemMessage
from thoughts.operations.core import Operation
from thoughts.operations.rules import LogicRule
from thoughts.operations.thought import Thought
from thoughts.parser import ConfigParser

class Choice(Operation):
    def __init__(self, options: list, repeat: bool = False):
        self.repeat = repeat
        self.options = options
        self.condition = None
    def execute(self, context: Context, message = None): 
        option: Operation = None
        for option in self.options:
            condition: Operation = option.condition
            # no condition - default to true
            if condition is None:
                break
            # condition exists - check if it's true
            _, truth = condition.execute(context, message)
            if truth == True:
                break
        if option is not None:
            if isinstance(option, LogicRule):
                return option.execute_actions(context, truth, message)
            return option.execute(context, message)
        return None, None
    @classmethod
    def parse_json(cls, json_snippet, config):
        repeat = json_snippet.get("repeat", False)
        items = ConfigParser.parse_operations(json_snippet["options"], config)
        # items = []
        # for item in json_snippet["options"]:
        #     if "Thought" in item:
        #         items.append(Thought.parse_json(item, config))
        #     elif "When" in item:
        #         items.append(LogicRule.parse_json(item, config))
        return cls(options=items, repeat=repeat)

class LLMRoutingAgent(Operation):
    def __init__(self, agents: list, routing_prompt: str):
        super().__init__(description="LLM Routing Agent")
        self.agents = agents
        self.routing_prompt = routing_prompt

    def execute(self, context: Context, message = None):
        # Construct the routing prompt with descriptions of all agents
        routing_message = SystemMessage(content=self.routing_prompt)
        agent_descriptions = "\n".join([f"{agent.__class__.__name__}: {agent.description}" for agent in self.agents])
        routing_message.content += f"\n\nAvailable agents:\n{agent_descriptions}"
        messages = [routing_message]

        # Append the incoming message if there is one
        if message is not None:
            messages.append(message)

        # Run the routing prompt against the LLM to decide which agent to call
        ai_message = context.llm.invoke(messages, stream=False)
        decision = ai_message.content.strip()

        # Find the corresponding agent based on the decision
        selected_agent = None
        for agent in self.agents:
            if agent.__class__.__name__ == decision:
                selected_agent = agent
                break

        if selected_agent is None:
            raise ValueError(f"No matching agent found for decision: {decision}")

        # Execute the selected agent and return its result
        return selected_agent.execute(context, message)