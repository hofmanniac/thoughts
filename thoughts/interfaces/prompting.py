# from thoughts.interfaces.llm import LLM
from thoughts.interfaces.memory import Memory
from thoughts.interfaces.config import Config
import json

# def build_from_template(prompt: dict, memory: Memory, message: dict = None, num_messages = 4):
#     prompt = substitute_variables(prompt, memory, message)
#     prompt = add_message_history(prompt, memory, num_messages)
#     prompt = add_message(prompt, message)
#     return prompt

# def build(prompt_name: str, memory: Memory, message: dict = None, num_messages = 4):
#     prompt = load_template(prompt_name)
#     prompt = build_from_template(prompt, memory, message, num_messages)
#     return prompt
    
# def build_prompt(prompt_name: str, memory: Memory, message=None, num_chat_history = 0):
#     prompt_template = load_template(prompt_name)
#     prompt = build_from_template(prompt_template, memory, message, num_messages=num_chat_history)
#     return prompt

# def substitute(lines, memory: Memory, message):
#     new_lines = []
#     for line in lines:

#         if str.startswith(line, "{"):

#             line = str.strip(line).removeprefix("{").removesuffix("}")

#             if str.strip(line) == "semantic-search":
#                 memories = memory.find("personal", message)
#                 for memory in memories:
#                     new_lines.append("- " + memory + "\n")
#                 continue

#             value = memory.get_item(line)
#             if type(value) is str:
#                 new_lines.append(value)
#             elif type(value) is dict:
#                 value = substitute(value["content"], memory, message)

#             if type(value) is list:
#                 new_lines.extend(value)

#             continue
        
#         new_lines.append(line)

#     return new_lines

# def substitute_variables(prompt, memory: Memory, message=None):
#     prompt["content"] = substitute(prompt["content"], memory, message)
#     return prompt
    
def get_text(prompt: dict):
    prompt_content = prompt["content"]
    content = "".join(prompt_content)
    return content

def add_message_history(prompt, memory: Memory, num_messages):
    chat_history = memory.recall_conversation_history(num_messages)
    if "messages" not in prompt:
        prompt["messages"] = []
    prompt["messages"].extend(chat_history)
    return prompt

def add_message(prompt, message):
    if message is not None:
        prompt["messages"].append(message)
    return prompt
    
def load_template(prompt_name: str):
    config = Config()
    config_path = config.values["data-path"]
    path = config_path + "/prompts/" + prompt_name + ".txt"
    with open(path, "r") as f:
        prompt_lines = f.readlines()
    prompt = {"content": prompt_lines, "messages": []}
    return prompt

def load(prompt_name: str):
    prompt_path = get_prompt_path(prompt_name)
    with open(prompt_path) as file:
        prompt_config = json.load(file)
    return prompt_config

# def get_prompt_template(prompt_name: str):
#     path = get_prompt_path(prompt_name)
#     return load_prompt(path)

def get_prompt_path(prompt_name: str):
    return "prompts/" + prompt_name + ".json"

# def parse_param(param):
#     parm_parts = str.split(param, ".")
#     source = parm_parts[0]
#     key = parm_parts[1]
#     return source, key

# def construct(prompt_name, message, memory: Memory):
#     prompt_path = get_prompt_path(prompt_name)
#     with open(prompt_path) as file:
#         prompt_config = json.load(file)

#     template = prompt_config["template"]
#     template_text = " ".join(template)

#     for param in template["params"]:
#         source, key = parse_param(param)
#         if source == "memory":
#             memories = memory.find(key, message)
#             memory_text = "\n- ".join(memories)
#             template_text = template_text.replace("\{param\}", memory_text)

#     return {"system": template_text}

# def construct_prompt(prompt_name: str, context: str = None):
#     prompt_template = load_prompt("prompts/" + prompt_name + ".json")
#     prompt_text = None
#     if context is not None:
#         prompt_text = prompt_template.format(context=context)
#     else:
#         prompt_text = prompt_template.format()
#     return prompt_text


# def construct_prompt_messages(
#     system_message: dict, recent_conversation_history: list = None, human_message: dict = None
# ):
#     prompt_messages = []
#     prompt_messages.append(system_message)

#     if recent_conversation_history is not None:
#         prompt_messages.extend(recent_conversation_history)

#     if human_message is not None:
#         prompt_messages.append(human_message)

#     return prompt_messages

# class PromptRunner:
#     llm: LLM = None
#     memory: Memory = None
#     messages_since_last_run: int = 0
#     run_every: int = 0
#     num_chat_history: int = 0

#     def __init__(self, llm, memory, run_every = 1, num_chat_history = 4):
#         self.llm = llm
#         self.memory = memory
#         self.messages_since_last_run = 0
#         self.run_every = run_every
#         self.num_chat_history = num_chat_history

#     def execute(self, prompt_name: str, message=None, add_to_chat_history=True):
#         self.messages_since_last_run += 1
#         if self.messages_since_last_run < self.run_every:
#             return None
#         prompt_template = load_template(prompt_name)
#         prompt = build_from_template(prompt_template, self.memory, message, num_messages=self.num_chat_history)
#         response = self.llm.respond(prompt)

#         if add_to_chat_history:
#             self.memory.add_chat_history(message)
#             self.memory.add_chat_history(response)

#         return response
    
#     def resume_or_start(self, runner_starts=True, start_prompt=None, continue_prompt=None, add_to_chat_history=True):
#         self.memory.load_previous_messages()
#         last_message = self.memory.get_chat_history(1)
#         ai_message = last_message if last_message is not None and last_message["speaker"] == "AI" else None
#         human_message = last_message if last_message is not None and last_message["speaker"] == "Human" else None

#         if ai_message is None and human_message is None and runner_starts:
#             ai_message = self.execute(start_prompt, human_message, add_to_chat_history=add_to_chat_history)
#             return ai_message, False
#         elif ai_message is not None:
#             return ai_message, True
#         elif human_message is not None:
#             ai_message = self.execute(continue_prompt, human_message, add_to_chat_history=add_to_chat_history)
#             return ai_message, False
#         return None, False