
import os
from openai import AzureOpenAI
from openai import OpenAI
import thoughts.interfaces.messaging
from thoughts.interfaces.messaging import HumanMessage, AIMessage, PromptMessage, SystemMessage
import thoughts.interfaces.prompting
from thoughts.interfaces.config import Config

class LLM:

    def __init__(self, max_retries = 3):
        print("Loading language model...")

        app_config = Config()
        
        self.llm_platform = app_config.values["llm-platform"]
        self.config = app_config.values[self.llm_platform]

        if self.config["type"] == "cloud":
            self.client = AzureOpenAI(
                azure_endpoint = self.config["endpoint"], 
                api_key = self.config["key"],  
                api_version = self.config["model"])
        else:
            self.client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

        self.max_retries = max_retries

    def invoke(self, messages: list, stream = False, json=False, temperature=0.8):

        api_messages = []
        message: PromptMessage = None
        for message in messages:
            api_message = message.format_for_api()
            api_messages.append(api_message)

        num_retries = 0
        completed = False
        response_format = {"type": "json_object"} if json else None

        while not(completed) and num_retries <= self.max_retries:
            try:

                if self.config["type"] == "local":
                    completion = self.client.chat.completions.create(
                        model=self.config["model"],
                        # model="TheBloke/phi-2-GGUF",
                        messages=api_messages,
                        temperature=temperature,
                        stream=stream,
                        response_format=response_format
                    )
                    
                elif self.config["type"] == "cloud":
                    completion = self.client.chat.completions.create(
                        model = self.config["deployment"],
                        messages = api_messages,
                        response_format=response_format,
                        temperature=temperature,
                        stream=stream)
                
                completed = True
            except  Exception as e:
                print(f"Exception type: {type(e).__name__}")
                print(f"Exception message: {e}")
                num_retries += 1

        if stream:
            ai_message = AIMessage(completion=completion)
        else:
            response_text = completion.choices[0].message.content
            ai_message = AIMessage(content = response_text)

        return ai_message
    
    def respond_to_text(self, text, stream = False):
        system_message = SystemMessage()
        messages = [system_message]
        instruction = HumanMessage(content=text)
        messages.append(instruction)
        response = self.invoke(messages, stream)
        return response
    
    def respond(self, prompt, stream = False):

        if type(prompt) is dict:

            core_text = thoughts.interfaces.prompting.get_text(prompt)

            if "context" in prompt:
                context_text = "\n\nContext:"
                for part in prompt["context"]:
                    part_text = "\n -".join(part["items"])
                    context_text += part_text
                prompt_text = core_text + context_text
            else:
                prompt_text = core_text

            system_message = SystemMessage(content=prompt_text)

            messages = [system_message]
            chat_messages = prompt["messages"] if "messages" in prompt else []
            messages.extend(chat_messages)
            
        elif type(prompt) is list:
            messages = prompt

        response = self.invoke(messages, stream)
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


    # def invoke_local(self, messages: list, stream_and_write = False):

    #     # Chat with an intelligent assistant in your terminal
    
    #     # Point to the local server
    #     # client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

    #     api_messages = []
    #     message: PromptMessage = None
    #     for message in messages:
    #         api_message = message.format_for_api()
    #         api_messages.append(api_message)

    #     while True:
    #         completion = self.client.chat.completions.create(
    #             model=self.config["model"],
    #             # model="TheBloke/phi-2-GGUF",
    #             messages=api_messages,
    #             temperature=0.8,
    #             stream=stream_and_write,
    #         )

    #         if stream_and_write:
    #             new_message = {"role": "assistant", "content": ""}
    #             for chunk in completion:
    #                 if chunk.choices[0].delta.content:
    #                     print(chunk.choices[0].delta.content, end="", flush=True)
    #                     new_message["content"] += chunk.choices[0].delta.content
    #             response_text = new_message["content"]
    #         else:
    #             response_text = completion.choices[0].message.content

    #         ai_message = AIMessage(content = response_text)
    #         return ai_message

    # def invoke_cloud(self, messages: list, stream_and_write = False):

    #     api_messages = []
    #     message: PromptMessage = None
    #     for message in messages:
    #         api_message = message.format_for_api()
    #         api_messages.append(api_message)

    #     num_retries = 0
    #     completed = False

    #     while not(completed) and num_retries <= self.max_retries:
    #         try:
    #             completion = self.client.chat.completions.create(
    #                 model = self.config["deployment"],
    #                 messages = api_messages,
    #                 stream=stream_and_write)
                
    #             completed = True
    #         except  Exception as e:
    #             print(f"Exception type: {type(e).__name__}")
    #             print(f"Exception message: {e}")
    #             num_retries += 1

    #     if stream_and_write:
    #         new_message = {"role": "assistant", "content": ""}
    #         for chunk in completion:
    #             if len(chunk.choices) == 0:
    #                 continue
    #             if chunk.choices[0].delta.content:
    #                 print(chunk.choices[0].delta.content, end="", flush=True)
    #                 new_message["content"] += chunk.choices[0].delta.content
    #         response_text = new_message["content"]
    #     else:
    #         response_text = completion.choices[0].message.content

    #     ai_message = AIMessage(content = response_text)
    #     return ai_message
    
    # def invoke(self, messages: list, stream_and_write = False):

    #     if self.config["type"] == "local":
    #         return self.invoke_local(messages, stream_and_write)
    #     elif self.config["type"] == "cloud":
    #         return self.invoke_cloud(messages, stream_and_write)
