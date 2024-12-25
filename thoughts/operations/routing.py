from thoughts.engine import Context
from thoughts.interfaces.messaging import SystemMessage
from thoughts.operations.core import Operation

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