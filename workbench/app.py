import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from time import sleep
import streamlit as st

from thoughts.agents.chat import ChatAgent
from thoughts.engine import Context
from thoughts.interfaces.messaging import HumanMessage

def main():

    agent1_context = Context(prompt_path="chat")
    agent1 = ChatAgent(context=agent1_context, prompt_name="chat-continue", handle_io=False)

    agent2_context = Context(prompt_path="prompts")
    agent2 = ChatAgent(context=agent2_context, prompt_name="pirate", handle_io=False)

    st.title("My First Streamlit App")
    st.write("Hello, welcome to my app!")
    
    if st.button("Click me!"):
        agent2_message = HumanMessage(content="Tell me a funny story.")

        while True:
            agent2_message = HumanMessage(content=agent2_message.content)
            agent1_message, control = agent1.execute(agent1_context, message=agent2_message)
            print(agent1_message.content)
            st.write("AGENT 1: " + agent1_message.content)
            sleep(2)

            agent1_message = HumanMessage(content=agent1_message.content)
            agent2_message, control = agent2.execute(agent2_context, message=agent1_message)
            print(agent2_message.content)
            st.write("AGENT 2: " + agent2_message.content)
            sleep(2)

if __name__ == "__main__":
    main()


