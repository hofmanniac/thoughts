import json
from thoughts.agent import Agent
from thoughts.context import Context
from thoughts.interfaces.llm import LLM
from thoughts.interfaces.messaging import HumanMessage

class Cortex:

    def __init__(self, name: str):
        self.name = name
        self.llm = LLM()
        self.description = ""
        self.agents = []
        self.context: Context = Context(llm=self.llm)
        self.load_from_config()

    def respond(self, prompt):
        responses = []
        agent: Agent
        message = HumanMessage(content=prompt)
        self.context.push_message(message)
        for agent in self.agents:
            agent_response = agent.execute(self.context, message)
            responses.extend(agent_response.messages)
        return responses
    
    def load_from_config(self):
        with open(f".workspaces/{self.name}/config.json", 'r') as file:
            config = json.load(file)
        self.description = config.get("description", "")
        for agent_path in config.get("agents", []):
            agent = Agent.load_from_config(self.context, agent_path)
            self.agents.append(agent)
        