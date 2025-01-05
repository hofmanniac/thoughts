
from thoughts.context import Context
from thoughts.operations.core import Operation
from thoughts.interfaces.messaging import HumanMessage, SystemMessage
from thoughts.operations.prompting import PromptConstructor
from thoughts.parser import ConfigParser
from thoughts.util import console_log

class Thought(Operation):

    def __init__(self, name, train, save_into = None, run_every = 1, output = False, condition = None):
        self.name = name
        self.train: PromptConstructor = train
        self.started = False
        self.save_into = save_into
        self.run_every = run_every
        self.num_since_last_run = 0
        self.messages = []
        self.output = output
        self.condition = condition

    def execute(self, context: Context, message = None):

        # check if it's time to run
        self.num_since_last_run += 1   
        if self.num_since_last_run < self.run_every:
            return message, None
        self.num_since_last_run = 0

        messages, control = self.train.execute(context, message)

        if True:
            for message in messages:
                if isinstance(message, SystemMessage):
                    console_log(message.content, "magenta")
                else:
                    console_log(f'[{type(message)}]', "magenta")

        # invoke AI
        ai_message = context.llm.invoke(messages, stream=True)

        # mark as started (after the first run)
        self.started = True

        # display result
        if self.output:
            console_log("", "green")
            console_log(f'{self.name}: {ai_message.content}', "green")

        # save into
        if self.save_into is not None:
            context.set_item(self.save_into, ai_message.content)

        # append AI message
        context.messages.append(ai_message)
        return ai_message, None
    
    # def execute1(self, context: Context, message = None):

    #     # check if it's time to run
    #     self.num_since_last_run += 1   
    #     if self.num_since_last_run < self.run_every:
    #         return message, None
    #     self.num_since_last_run = 0

    #     messages = []
    #     system_prompt = SystemMessage("")
    #     system_prompt.content = ""
    #     instruction_prompt = HumanMessage("")
    #     current_prompt = system_prompt

    #     for step in self.train:
    #         if type(step) is str:
    #             current_prompt.content += f"\n{step}"
    #         elif "Role" in step:
    #             current_prompt.content += f"\n{step['Role']}"
    #         elif "Recall" in step:
    #             context_item = context.get_item(step["Recall"])
    #             if context_item is None:
    #                 context_item = "NA"
    #             title = step["as"]
    #             current_prompt.content += f"\n\n{title}:\n{context_item}"
    #         elif "Start" in step:
    #             if len(context.messages) == 0 or message is None:
    #                 if message is None:
    #                     current_prompt = instruction_prompt
    #                 current_prompt.content += f"\n{step['Start']}"
    #         elif "Continue" in step:
    #             if len(context.messages) > 0:
    #                 system_prompt.content += f"\n{step['Continue']}"
    #         elif "History" in step:
    #             num_messages = step.get("History", 0) # can also be True or False
    #             if type(num_messages) is bool and num_messages == True:
    #                 history = context.messages
    #             else:
    #                 history = context.messages[-1 * num_messages:]
    #             messages.extend(history)
    #             current_prompt = instruction_prompt
    #         elif "Instruction" in step:
    #             current_prompt = instruction_prompt
    #             current_prompt.content += f"\n{step['Instruction']}"

    #     if system_prompt.content == "":
    #         system_prompt.content = "You are a helpful AI assistant."

    #     messages.insert(0, system_prompt)
    #     # if message is not None:
    #     #     messages.append(HumanMessage(message.content))
    #     if instruction_prompt.content != "":
    #         messages.append(instruction_prompt)
    #         context.messages.append(instruction_prompt)

    #     # invoke AI
    #     ai_message = context.llm.invoke(messages, stream=True)

    #     # display result
    #     print("\n")
    #     print(self.name, ": ", ai_message.content, sep="")

    #     # save into
    #     if self.save_into is not None:
    #         context.set_item(self.save_into, ai_message.content)

    #     # append AI message
    #     context.messages.append(ai_message)
    #     return ai_message, None
    
    @classmethod
    def parse_json(cls, json_snippet, config):

        name = json_snippet.get("Thought", None)
        save_into = json_snippet.get("into", None)
        run_every = json_snippet.get("runEvery", 1)
        output = json_snippet.get("output", False)

        condition_config = json_snippet.get("when", None)
        condition = ConfigParser.parse_logic_condition(condition_config)

        thought = cls(name=name, train=None, save_into=save_into, run_every=run_every, output=output, condition=condition)
    
        # delay parsing the train config until the thought is executed
        train_config = json_snippet.get("train", [])
        train = PromptConstructor.parse_json(train_config, config, thought)
        thought.train = train
        return thought

    
class AnalyzeMessages(Operation):
    def __init__(self, name, role, instruction):
        self.name = name
        self.role = role
        self.instruction = instruction
        self.condition = None

    def execute(self, context: Context, messages = None):

        # begin system prompt
        llm_messages = []
        llm_messages.append(SystemMessage(f"{self.role} {self.instruction}"))

        # add history
        if type(messages) is list:
            llm_messages.extend(messages)
        else:
            llm_messages.append(messages)

        # append instruction
        instruction_message = HumanMessage(self.instruction)
        llm_messages.append(instruction_message)

        # invoke AI
        ai_message = context.llm.invoke(llm_messages, stream=True)

        print("\n")
        print(self.name, ": ", ai_message.content, sep="")

        # append AI message
        return ai_message, None
    
    @classmethod
    def parse_json(cls, json_snippet, config):

        name = json_snippet.get("Analyze", None)
        
        instruction = json_snippet.get("instruction", "Analyze the messages in this conversation.")
        
        agent = next(agent for agent in config["Agents"] if agent["Agent"] == name)
        role = agent["role"]  

        return cls(name=name, role=role, instruction=instruction)