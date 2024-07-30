from datetime import datetime
import json
import os
from thoughts.engine import Context, PipelineExecutor
from thoughts.interfaces.messaging import HumanMessage
from thoughts.operations.core import Operation
from thoughts.operations.prompting import PromptConstructor, PromptRunner, StaticContentLoader, StaticPromptLoader

class RAGContextAdder(Operation):

    def __init__(self, collection_name: str, title: str):
        self.collection_name = collection_name
        self.title = title

    def execute(self, context: Context, message = None):

        search_message = message if message is not None else context.get_last_message()
        memories = context.memory.find(self.collection_name, search_message)
        
        prompt = context.get_item("prompt")
        if "context" not in prompt:
            prompt["context"] = []
        
        rag_context = {"context": self.collection_name, "items": memories}
        prompt["context"].append(rag_context)
        
        return rag_context, None
    
class MemoryKeeper(Operation):
    def __init__(self, item_key: str = ""):
        self.condition = None
        self.item_key = item_key
    def execute(self, context: Context, message = None):
        if message is not None:
            context.append_item(self.item_key, message.content)
        return None, None

class MemoryRetriever(Operation):
    def __init__(self, key: str, title: str, instructions: str = None):
        self.key = key
        self.title = title
        self.instructions = instructions
    def execute(self, context: Context, message = None):
        items = context.get_item(self.key)
        if items is None:
            return None, None
        return items, None
    
class MessagesSummarizer(Operation):
    
    def __init__(self, prompt_name: str = "", num_messages: int = 0, store_into: str = None):
        self.condition = None
        self.prompt_name = prompt_name
        self.num_messages = num_messages
        summary_prompt = PromptConstructor([StaticPromptLoader(self.prompt_name)])

        self.summarizer = PromptRunner(
            prompt_constructor=summary_prompt, 
            num_chat_history=self.num_messages * 2, 
            run_every=self.num_messages, 
            append_history=False, 
            run_as_message=True, 
            stream=False)
        
        self.store_into = store_into

    def execute(self, context: Context, message = None):
        summary, control = self.summarizer.execute(context)
        if summary is not None and self.store_into is not None:
            context.append_item(self.store_into, summary.content)
        return summary, None

class InformationExtractor(Operation):

    def __init__(self, extractor_prompt: str):
        self.extractor_prompt = extractor_prompt

    def _extract_info(self, context: Context, content):

        extractor_persona = StaticPromptLoader(self.extractor_prompt)
        extractor_content = StaticContentLoader(content=content)
        extractor = PromptConstructor([extractor_persona, extractor_content])

        runner = PromptRunner(prompt_constructor=extractor, run_as_message=True)
        conclusions, control = runner.execute(context)

        return conclusions

    def execute(self, context: Context, message = None):

        # check if already ran
        # todo - set a switch to force this to be recreated
        conclusions = context.get_item(self.extractor_prompt, None)
        if conclusions is not None:
            return conclusions, None
        
        content = context.get_item("summary")

        extractor_persona = StaticPromptLoader(self.extractor_prompt)
        extractor_content = StaticContentLoader(content=content)
        extractor = PromptConstructor([extractor_persona, extractor_content])

        runner = PromptRunner(prompt_constructor=extractor, run_as_message=True)
        conclusions, control = runner.execute(context)

        context.set_item(self.extractor_prompt, conclusions.content)
        return conclusions, None
    
class SessionIterator(Operation):
    def __init__(self, operations: list, num_previous: int = None):
        self.operations = operations
        self.num_previous = num_previous

    def get_last_n_folders(self, directory, n):
        # Get a list of all folders in the directory
        all_folders = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]

        # Filter out folders that don't match the yyyy-mm-dd format
        valid_folders = []
        for folder in all_folders:
            try:
                datetime.strptime(folder, '%Y-%m-%d')
                valid_folders.append(folder)
            except ValueError:
                continue

        # Sort the folders in reverse chronological order
        valid_folders.sort(reverse=True)

        # Return the last N folders
        if n is None:
            return valid_folders

        return valid_folders[:n]
    
    def execute(self, context: Context, message = None):
        folders = self.get_last_n_folders("memory/sessions", self.num_previous)
        results = []
        for folder in folders:
            session_id = folder

            # execution context is a mashup of the persisted session and the session passed in
            execution_context = Context(llm=context.llm, memory=context.memory, 
                                        prompt_path=context.prompt_path, session_id=session_id, persist_session=context.persist_session)
            
            operation: Operation = None
            for operation in self.operations:
                result, control = operation.execute(execution_context, message)
                results.append(result)

        return results, None




