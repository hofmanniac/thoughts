from thoughts.engine import Context
from thoughts.operations.core import Operation

class RAGContextAdder(Operation):

    def __init__(self, collection_name: str):
        self.collection_name = collection_name

    def execute(self, context: Context):

        last_message = context.get_last_message()
        memories = context.memory.find(self.collection_name, last_message)
        
        prompt = context.get("prompt")
        if "context" not in prompt:
            prompt["context"] = []
        
        rag_context = {"context": self.collection_name, "items": memories}
        prompt["context"].append(rag_context)
        
        return rag_context
        