from datetime import datetime
import json
import os
from thoughts.engine import Context, PipelineExecutor
from thoughts.interfaces.messaging import HumanMessage, PromptMessage
from thoughts.operations.core import Operation
from thoughts.operations.prompting import MessagesBatchAdder, PromptAppender, PromptConstructor, PromptRunner, PromptStarter, StaticContentLoader, StaticPromptLoader

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
    
    def __init__(self, prompt_name: str = "", batch_size: int = 0, store_into: str = None, allow_partial_batch=True):
        self.condition = None
        self.prompt_name = prompt_name
        self.batch_size = batch_size
        self.store_into = store_into
        self.allow_partial_batch = allow_partial_batch

    def execute(self, context: Context, message = None):

        # Load existing summaries and processed message indices if the file exists
        data = context.get_item(self.store_into)
        if data is None:
            data = {"content": [], "ids": set()}
        else:
            data = {"content": data["content"], "ids": set(data["ids"])}
        
        summaries: list = data.get("content", [])
        processed_ids: set = data.get("ids", set())

        loop: bool = True
        while loop:

            messages, control = PromptStarter(
            content="You are a helpful AI assistant.").execute(context)

            # will keep adding the next set of messages in batch to the messages
            messages, loop = MessagesBatchAdder(
                self.batch_size, exclude_ids=processed_ids, 
                allow_partial_batch=self.allow_partial_batch).execute(context, messages)
            
            if loop == False:
                continue

            messages, control = PromptStarter(
            role="human", prompt_name=self.prompt_name).execute(context, messages)

            summary, control = PromptRunner(
            stream=False, append_history=False).execute(context, messages)

            summaries.append(summary.content)

            indices = [message.message_id for message in messages]
            processed_ids.update(indices)

        # Save the updated summaries and processed indices to the JSON file
        result = {"content": summaries, "ids": list(processed_ids)}
        context.set_item(self.store_into, result)
        return result, None
    
    def execute2(self, context: Context, message = None):

        # Load existing summaries and processed message indices if the file exists
        data = context.get_item(self.store_into)
        if data is None:
            data = {"content": [], "ids": set()}
        
        summaries: list = data.get("content", [])
        processed_ids: set = data.get("ids", set())

        # Find the next batch of messages to process
        new_messages = [(i, msg) for i, msg in enumerate(context.messages) if i not in processed_ids]
        if not new_messages:
            return None, None

        if len(new_messages) < self.batch_size:
            return None, None
        
        batches = [new_messages[i:i + self.batch_size] for i in range(0, len(new_messages), self.batch_size)]
        for batch in batches:
            
            messages, control = PromptStarter(
                content="You are a helpful AI assistant.").execute(context)
            
            indices, batch_messages = zip(*batch)
            messages.extend(batch_messages)

            messages, control = PromptStarter(
                role="human", prompt_name=self.prompt_name).execute(context, messages)
            
            summary, control = PromptRunner(
                stream=False, append_history=False).execute(context, messages)

            summaries.append(summary)
            processed_ids.update(indices)

        # Save the updated summaries and processed indices to the JSON file
        context.set_item(self.store_into, {"content": summaries, "ids": list(processed_ids)})

        context.log(f"Processed {len(new_messages)} new messages in {len(batches)} batches.")

    def execute_old(self, context: Context, message = None):
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




