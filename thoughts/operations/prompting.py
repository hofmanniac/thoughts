from thoughts.operations.core import Operation
import thoughts.interfaces.prompting
from thoughts.engine import Context


class StaticPromptLoader(Operation):
    def __init__(self, prompt_name: str):
        self.prompt_name = prompt_name

    def execute(self, context: Context):
        prompt = thoughts.interfaces.prompting.load_template(self.prompt_name)
        context.set("prompt", prompt)


# class MessageHistoryAdder(Operation):
#     def __init__(self, num_messages: int = 0):
#         self.num_messages = num_messages
#     def execute(self, context: Context):
#         prompt = context.get("prompt")
#         messages = context.peek(self.num_messages)
#         prompt["messages"].extend(messages)


class PromptConstructor(Operation):
    def __init__(self, operations: list):
        self.operations = operations

    def execute(self, context: Context):
        operation: Operation
        for operation in self.operations:
            operation.execute(context)


class PromptRunner(Operation):
    def __init__(
        self,
        prompt_name: str = None,
        prompt_constructor: PromptConstructor = None,
        num_chat_history=0,
    ):
        self.prompt_name = prompt_name
        self.num_chat_history = num_chat_history
        self.prompt_constructor = prompt_constructor

    def execute(self, context: Context):
        # message = context.peek()

        if self.prompt_constructor is None:
            static_prompt_loader = StaticPromptLoader(self.prompt_name)
            prompt_constructor = PromptConstructor([static_prompt_loader])
        else:
            prompt_constructor = self.prompt_constructor

        prompt_constructor.execute(context)
        prompt = context.get("prompt")

        # prompt = thoughts.interfaces.prompting.load_template(self.prompt_name)
        # prompt = interfaces.prompting.build_prompt(self.prompt_name, context.memory, message, self.num_chat_history)
        message_history = context.peek(self.num_chat_history)
        prompt["messages"] = message_history
        ai_message = context.llm.respond(prompt)
        context.push(ai_message)
        return ai_message


class PromptResumer(Operation):
    def __init__(
        self,
        start_prompt_name,
        continue_prompt_name,
        start_if_no_messages=True,
        add_to_chat_history=True,
    ):
        self.start_prompt_name = start_prompt_name
        self.continue_prompt_name = continue_prompt_name
        self.start_if_no_messages = start_if_no_messages
        self.add_to_chat_history = add_to_chat_history

    # def execute(self, context: Context):

    #     context.memory.load_previous_messages()
    #     last_messages = context.memory.get_chat_history(1)
    #     last_message = last_messages[0] if len(last_messages) > 0 else None
    #     ai_message = last_message if last_message is not None and last_message["speaker"] == "AI" else None
    #     human_message = last_message if last_message is not None and last_message["speaker"] == "Human" else None

    #     if ai_message is None and human_message is None and self.start_if_no_messages:
    #         prompt = interfaces.prompting.build_prompt(self.start_prompt_name, context.memory)
    #         ai_message = context.llm.respond(prompt)
    #         if self.add_to_chat_history:
    #             context.memory.add_chat_history(ai_message)
    #             context.push(ai_message)
    #         return ai_message, False

    #     elif ai_message is not None:
    #         return ai_message, True

    #     elif human_message is not None:
    #         prompt = interfaces.prompting.build_prompt(self.continue_prompt_name, context.memory, human_message)
    #         ai_message = context.llm.respond(prompt)
    #         if self.add_to_chat_history:
    #             context.memory.add_chat_history(ai_message)
    #             context.push(ai_message)
    #         return ai_message, False

    #     return None, False

    def execute(self, context: Context):
        context.memory.load_previous_messages()
        last_messages = context.memory.get_chat_history(1)
        last_message = last_messages[0] if last_messages else None

        if last_message:
            if last_message["speaker"] == "AI":
                return last_message, True
            elif last_message["speaker"] == "Human":
                prompt_name = self.continue_prompt_name
                human_message = last_message
        else:
            if self.start_if_no_messages:
                prompt_name = self.start_prompt_name
                human_message = None
            else:
                return None, False

        prompt = thoughts.interfaces.prompting.build_prompt(
            prompt_name, context.memory, human_message
        )
        ai_message = context.llm.respond(prompt)
        if self.add_to_chat_history:
            context.memory.add_chat_history(ai_message)
            context.push(ai_message)

        return ai_message, False
