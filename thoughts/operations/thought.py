
import datetime
from thoughts.context import Context
from thoughts.operations.console import ConsoleWriter
from thoughts.operations.core import Operation
from thoughts.interfaces.messaging import HumanMessage, SystemMessage
from thoughts.operations.prompting import PromptConstructor
from thoughts.parser import ConfigParser
from thoughts.util import console_log

# class Thought(Operation):

#     def __init__(self, name, train, save_into = None, run_every = 1, output = False, condition = None):
#         self.name = name
#         self.train: PromptConstructor = train
#         self.started = False
#         self.save_into = save_into
#         self.run_every = run_every
#         self.num_since_last_run = 0
#         self.messages = []
#         self.output = output
#         self.condition = condition

#     def execute(self, context: Context, message = None):

#         # check if it's time to run
#         self.num_since_last_run += 1   
#         if self.num_since_last_run < self.run_every:
#             return message, None
#         self.num_since_last_run = 0

#         messages, control = self.train.execute(context, message)

#         if True:
#             for message in messages:
#                 if isinstance(message, SystemMessage):
#                     console_log(message.content, "magenta")
#                 else:
#                     console_log(f'[{type(message)}]', "magenta")

#         # invoke AI
#         ai_message = context.llm.invoke(messages, stream=True)

#         # mark as started (after the first run)
#         self.started = True

#         # display result
#         if self.output:
#             console_log("", "green")
#             console_log(f'{self.name}: {ai_message.content}', "green")

#         # save into
#         if self.save_into is not None:
#             context.set_item(self.save_into, ai_message.content)

#         # append AI message
#         context.messages.append(ai_message)
#         return ai_message, None
    
#     @classmethod
#     def parse_json(cls, json_snippet, config):

#         name = json_snippet.get("Thought", None)
#         save_into = json_snippet.get("into", None)
#         run_every = json_snippet.get("runEvery", 1)
#         output = json_snippet.get("output", False)

#         condition_config = json_snippet.get("when", None)
#         condition = ConfigParser.parse_logic_condition(condition_config)

#         thought = cls(name=name, train=None, save_into=save_into, run_every=run_every, output=output, condition=condition)
    
#         # delay parsing the train config until the thought is executed
#         train_config = json_snippet.get("train", [])
#         train = PromptConstructor.parse_json(train_config, config, thought)
#         thought.train = train
#         return thought

class Thought(Operation):
    monikers = ["Thought"]
    def __init__(self, name, train, save_into=None, run_every=1, output=False, condition=None, config=None, channel=None):
        self.name = name
        self.train: PromptConstructor = train
        self.save_into = save_into
        self.run_every = run_every
        self.num_since_last_run = 0
        self.output = output
        self.condition = condition
        self.config = config
        self.channel = channel  # Optional; used for chaining outputs
        self.started = False

    def execute(self, context: Context, message=None):

        # Check if it's time to run
        self.num_since_last_run += 1
        if self.num_since_last_run < self.run_every:
            return message, None
        self.num_since_last_run = 0

        # Check condition
        # if self.condition and not self.condition.evaluate(context):
        #     return message, None

        # Generate prompt and invoke AI
        messages, control = self.train.execute(context, message, self)
        ai_message = context.llm.invoke(messages, stream=True)

        # Save into context
        if self.save_into:
            context.set_item(self.save_into, ai_message.content)

        # Append AI message to conversation
        context.push_message(ai_message)
        # context.messages.append(ai_message)

        # Optionally express the result
        if self.output:
            channel_name = self.channel or "Default"
            channels = self.config.get("Channels", {})
            if channel_name in channels:
                chain = channels[channel_name]
                operations = ConfigParser.parse_operations(chain, self.config)
                op: Operation = None
                for op in operations:
                    op.execute(context, ai_message)
            else:
                op = ConsoleWriter(ai_message.content)
                op.execute(context, ai_message)
                # print(ai_message.content)

        # Mark as started (after first run)
        self.started = True

        return ai_message, None

    @classmethod
    def parse_json(cls, json_snippet, config):

        # Extract thought name
        moniker = cls.get_first_moniker(json_snippet, cls.monikers)
        name = json_snippet.get(moniker, None)

        # determine if thought definition is inline or in the config
        train_config = json_snippet.get("train", None)
        # thought is defined in the config
        if train_config is None:
            # get the config thought definitions
            config_thoughts = config.get("Thoughts", None)
            if config_thoughts:
                # get the thought config by name
                thought_config = config_thoughts.get(name, None)
                # set the thought name
                thought_config[moniker] = name
                train_config = thought_config["train"]
        # thought is defined inline
        else:
            thought_config = json_snippet

        # Extract basic fields
        # prioritize using the json_snippet values, then the thought_config values, then the default values
        save_into = json_snippet.get("into", thought_config.get("into", None))
        run_every = json_snippet.get("runEvery", thought_config.get("runEvery", 1))
        output = json_snippet.get("output", thought_config.get("output", False))

        # Parse condition logic
        condition_config = json_snippet.get("when", thought_config.get("when", None))
        condition = ConfigParser.parse_logic_condition(condition_config)

        # Optional channel
        channel = json_snippet.get("channel", thought_config.get("channel", None))

        # Return an instance of Thought
        thought = cls(
            name=name,
            train=None,
            save_into=save_into,
            run_every=run_every,
            output=output,
            condition=condition,
            config=config,
            channel=channel
        )

        # delay parsing the train config until the thought is executed
        train = PromptConstructor.parse_json(train_config, config)
        thought.train = train

        return thought

class Express(Thought):
    monikers = ["Express"]
    def __init__(self, *args, channel=None, **kwargs):
        # Force output to True and set channel as required
        kwargs["output"] = True
        super().__init__(*args, **kwargs)
        self.channel = channel

    def execute(self, context: Context, message=None):
        # Reuse Thought's execution logic
        return super().execute(context, message)

    @classmethod
    def parse_json(cls, json_snippet, config):
        # Use Thought's parse_json for shared fields
        thought = super().parse_json(json_snippet, config)

        # Ensure 'channel' is set in Express JSON
        channel = json_snippet.get("channel", None)
        # if not channel:
        #     raise ValueError("The 'channel' field is required for an Express node.")

        # Return an Express instance
        return cls(
            name=thought.name,
            train=thought.train,
            save_into=thought.save_into,
            run_every=thought.run_every,
            output=True,  # Force output to True
            condition=thought.condition,
            config=config,
            channel=channel
        )

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