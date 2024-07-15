
import os
from openai import AzureOpenAI
import thoughts.interfaces.messaging
from thoughts.interfaces.messaging import HumanMessage, AIMessage, PromptMessage, SystemMessage
import thoughts.interfaces.prompting
from thoughts.interfaces.config import Config

class LLM:

    def __init__(self):
        print("Loading language model...")

        app_config = Config()
        self.config = app_config.values["openai"]

        self.client = AzureOpenAI(
            azure_endpoint = self.config["endpoint"], 
            api_key = self.config["key"],  
            api_version = self.config["model"])
    
    def invoke(self, messages: list):

        api_messages = []
        message: PromptMessage = None
        for message in messages:
            api_message = message.format_for_api()
            api_messages.append(api_message)

        api_response = self.client.chat.completions.create(
            model = self.config["deployment"],
            messages = api_messages)

        response_text = api_response.choices[0].message.content
        ai_message = AIMessage(content = response_text)
        return ai_message
    
    def respond(self, prompt: dict):

        core_text = thoughts.interfaces.prompting.get_text(prompt)

        context_text = ""
        for part in prompt["context"]:
            part_text = "\n-".join(part["items"])
            context_text += part_text

        prompt_text = core_text + context_text
        system_message = SystemMessage(content=prompt_text)

        messages = [system_message]
        chat_messages = prompt["messages"] if "messages" in prompt else []
        messages.extend(chat_messages)

        response = self.invoke(messages)
        return response
    
    # def respond_to_text(self, text):
    #     response = self.invoke(text)
    #     return response.content
    
    # def respond_to_messages(self, prompt_messages: list):
    #     api_messages = self.convert_to_api_messages(prompt_messages)
    #     response = self.invoke(api_messages)
    #     response_text = response.content
    #     ai_message =  thoughts.interfaces.messaging.create_message("AI", response_text)
    #     return ai_message
    
    # def convert_to_api_messages(self, messages: list):
    #     api_messages = []
    #     for message in messages:
    #         if "system" in message:
    #             api_messages.append(SystemMessage(content=message["system"]))
    #             continue
    #         if message["speaker"] == "Human":
    #             api_messages.append(HumanMessage(content=message["text"]))
    #         elif message["speaker"] == "AI":
    #             api_messages.append(AIMessage(content=message["text"]))
    #     return api_messages
