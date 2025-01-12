from datetime import datetime
import os
import json
# import interfaces.logger
from chromadb.api import Collection
import logging
import warnings
import chromadb
# from chromadb.config import Settings
from copy import deepcopy
from chromadb.utils import embedding_functions
import nltk
from thoughts.interfaces.messaging import AIMessage, HumanMessage, PromptMessage

class SemanticClusters:
    def __init__(self):
        pass

class MemoryModule:

    def __init__(self):
        warnings.filterwarnings("ignore")
        logging.basicConfig(level=logging.CRITICAL)

        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the path to the root of the project
        self.project_root = os.path.abspath(os.path.join(script_dir, "../.."))

        self.chroma_client = chromadb.PersistentClient(path=self.project_root + "/memory/chroma")
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        self.messages = []

    def add_memory(self, collection: str, item):
        if type(item) is AIMessage or type(item) is HumanMessage or type(item) is PromptMessage:
            message = item
        elif type(item) is str:
            message = HumanMessage(content=item)
        message = self.add_embedding(message)
        # message = interfaces.logger.save_message(message, collection_name)
        collection = self.chroma_client.get_or_create_collection(collection)
        self.add_message_to_collection(collection, message, include_document=True)

    def add_embedding(self, message: PromptMessage):
        if message.embedding is not None:
            return message
        text = message.content
        embeddings = self.ef.embed_with_retries([text])
        message.embedding= embeddings[0]
        return message

    def add_message_to_collection(self, collection: Collection, message: PromptMessage, include_document: bool = False):
        embeddings = [message.embedding]
        documents = None
        if include_document:
            documents = [message.content]
        metadata = {"datetime": str(datetime.now())}
        ids = [message.message_id]
        collection.add(ids=ids, embeddings=embeddings, metadatas=[metadata], documents=documents)
        return message
       
class Memory:

    def __init__(self):
        warnings.filterwarnings("ignore")
        logging.basicConfig(level=logging.CRITICAL)

#         # self.llm = llm

        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the path to the root of the project
        project_root = os.path.abspath(os.path.join(script_dir, "../.."))

        self.chroma_client = chromadb.PersistentClient(path=project_root + "/memory/chroma")

#         print("Initializing embedding model...")
        self.ef = embedding_functions.DefaultEmbeddingFunction()

        self.ensure_punkt_tokenizer()

#         self.items = {}
#         self.chat_history = []

    def ensure_punkt_tokenizer(self):
        try:
            # Try to use the tokenizer, if it fails it means it's not downloaded
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            # Download the 'punkt' tokenizer if not found
            nltk.download('punkt')

    def erase_collection(self, collection_name):
        self.chroma_client.delete_collection(collection_name)

    def find(self, collection_name, message: PromptMessage):
        if message is None:
            return []
        return self.find_memories(message.content, collection_name)
    
    def find_memories(self, text: str, collection_name: str):
        sentences = self.split_into_sentences(text)
        memory_items = []
        for sentence in sentences:
            sentence_memory_items = self.query_vector_db(sentence, 6, collection_name)
            memory_items.extend(sentence_memory_items)
        memory_items = sorted(memory_items, key=lambda x: x["similarity"])

        texts = [x["text"] for x in memory_items]
        return texts
    
    def split_into_sentences(self, text):
        return nltk.sent_tokenize(text)
    
    def query_vector_db(self, text, num_results: int = 3, collection_name: str = "chats", where: dict = None):
        try:
            collection = self.chroma_client.get_collection(collection_name)
        except:
            return []
    
        search_results = collection.query(query_texts=[text], n_results=num_results, where=where)
        documents = search_results["documents"][0]
        distances = search_results["distances"][0]
        metadatas = search_results["metadatas"][0]
        idx = 0
        results = []
        for document in documents:
            if distances[idx] > 1.5:
                continue

            result = deepcopy(metadatas[idx])
            result["text"] = document
            result["similarity"] = distances[idx]
            # results.append({"text": document, "similarity": distances[idx]})
            results.append(result)
            # print(document, distances[idx])
            idx += 1
        return results

    def add_embedding(self, message: PromptMessage):
        if message.embedding is not None:
            return message
        text = message.content
        embeddings = self.ef.embed_with_retries([text])
        message.embedding= embeddings[0]
        return message

    def add(self, message: PromptMessage, collection_name: str):
        message = self.add_embedding(message)
        # message = interfaces.logger.save_message(message, collection_name)
        collection = self.chroma_client.get_or_create_collection(collection_name)
        self.add_message_to_collection(collection, message, include_document=True)

    def add_message_to_collection(self, collection: Collection, message: PromptMessage, include_document: bool = False):
        # modified = False

        # if message["text"] == "NA":
        #     return message, modified

        embeddings = [message.embedding]

        documents = None
        if include_document:
            documents = [message.content]

        metadata = {"datetime": str(datetime.now())}

        # if type(metadata["speaker"]) is list:
        #     metadata["speaker"] = "multiple"

        ids = [message.message_id]

        collection.add(ids=ids, embeddings=embeddings, metadatas=[metadata], documents=documents)

        # return message, modified
        return message

    # def persist_message(self, message: PromptMessage, collection_name: str):
    #     file_name = message.message_id
    #     message = self.save_log(message, collection_name, file_name + ".json")
    #     return message
    
    # def save_log(self, message: dict, collection_name: str, log_name: str):
    #     today_folder = get_todays_log_directory()
    #     directory = "memory/" + collection_name + "/" + today_folder
    #     if not os.path.exists(directory):
    #         os.makedirs(directory)

    #     filepath = directory + "/log-" + log_name
    #     with open(filepath, "w") as f:
    #         json.dump(message, f)

    #     message["file"] = filepath
    #     return message

# class Memory:
#     chat_history: list = None
#     chroma_client = None
#     ef: embedding_functions.SentenceTransformerEmbeddingFunction = None
#     # llm = None
#     items: dict = None

#     def set_item(self, name, value):
#         self.items[name] = value

#     def get_item(self, name):
#         if name not in self.items:
#             return None
#         return self.items[name]
    
#     def append_item(self, name, value):
#         if value is None:
#             return
#         if name not in self.items:
#             self.items[name] = []
#         self.items[name].append(value)

#     def add_chat_history(self, message):
#         if message is None:
#             return
#         self.chat_history.append(message)

#     def get_chat_history(self, num_messages = None):
#         if num_messages is None:
#             return self.chat_history
        
#         return self.chat_history[-1 * num_messages:]

#     def load_memory(self, rebuild_index=False):
#         # self.build_index_from_logs(rebuild_index, include_documents=True)

#         # global summarized_messages
#         # summarized_messages = []

#         self.chat_history = self.load_previous_messages()

#     def persist(self):
#         # self.chroma_client.persist()
#         pass



#     def remember_message(self, message: dict, collection_name: str):
#         message = self.add_embedding(message)
#         message = interfaces.logger.save_message(message, collection_name)
#         collection = self.chroma_client.get_or_create_collection(collection_name)
#         self.add_message_to_collection(collection, message, include_document=True)

#     def load_previous_messages(self):
#         log_messages = interfaces.logger.read_files("chats", log_folder=None)
#         return log_messages or []

#     def recall_conversation_history(self, k=4):
#         if self.chat_history is None:
#             return []
#         return self.chat_history[-1 * k :]

#     def remember_messages(self, messages: list, collection_name: str):
#         for message in messages:
#             self.remember_message(message, collection_name)

#         # self.conversation_history.extend(messages)

#     def list_memory(self, collection_name: str, k: int = 10, include_speakers: list = None):
#         result = []
#         collection = self.chroma_client.get_collection(collection_name)
#         items = collection.peek(k)
#         for idx, item in enumerate(items["metadatas"]):
#             if include_speakers is not None and item["speaker"] not in include_speakers:
#                 continue
#             memory_item = item
#             memory_item["text"] = items["documents"][idx]
#             result.append(memory_item)

#     def add_message_to_collection(self, collection: Collection, message: dict, include_document: bool = False):
#         modified = False

#         if message["text"] == "NA":
#             return message, modified

#         if "embedding" in message:
#             embeddings = [message["embedding"]]
#         else:
#             text = message["text"]
#             embeddings = self.ef._model.encode([text]).tolist()
#             message["embedding"] = embeddings[0]
#             modified = True

#         documents = None
#         if include_document:
#             documents = [message["text"]]

#         metadata = deepcopy(message)

#         if "text" in metadata:
#             del metadata["text"]

#         if "embedding" in metadata:
#             del metadata["embedding"]

#         if "sources" in metadata:
#             del metadata["sources"]

#         if type(metadata["speaker"]) is list:
#             metadata["speaker"] = "multiple"

#         ids = [metadata["file"]]

#         collection.add(ids=ids, embeddings=embeddings, metadatas=[metadata], documents=documents)

#         return message, modified

#     def load_messages(
#         self,
#         path: str,
#         collection_name: str,
#         persist: bool = False,
#         include_speakers: list = None,
#         include_documents=True,
#         rebuild_collection: bool = False,
#     ):
#         if rebuild_collection:
#             collection = self.chroma_client.get_or_create_collection(collection_name)
#             self.chroma_client.delete_collection(collection_name)

#         collection = self.chroma_client.get_or_create_collection(collection_name)

#         batches = interfaces.logger.generate_batches(path, batch_size=None)

#         for batch in batches:
#             for log_path in batch:
#                 # filename = os.path.basename(log_path)
#                 id = log_path.removesuffix(".json")
#                 id = id.replace("\\", "-")
#                 id = id.replace("/", "-")

#                 existing_embeddings = collection.get([id])
#                 if len(existing_embeddings["ids"]) > 0:
#                     continue

#                 print("Adding new memory to index - " + id + "...")
#                 with open(log_path, "r") as f:
#                     message = json.load(f)

#                 if str.startswith(message["text"], "NA"):
#                     continue

#                 message["file"] = id

#                 if include_speakers is not None and "speaker" in message:
#                     if message["speaker"] not in include_speakers:
#                         continue

#                 message, modified = self.add_message_to_collection(
#                     collection, message, include_document=include_documents
#                 )

#                 if modified == True:
#                     with open(log_path, "w") as f:
#                         json.dump(message, f)

#         if persist:
#             self.chroma_client.persist()

#     def load_messages_into_vector_db(
#         self,
#         path: str,
#         collection_name: str,
#         persist: bool = False,
#         include_speakers: list = None,
#         include_documents=True,
#     ):
#         # chroma_client.delete_collection(collection_name)
#         collection = self.chroma_client.get_or_create_collection(collection_name)

#         log_paths = interfaces.logger.list_files(path)

#         for log_path in log_paths:
#             filename = os.path.basename(log_path)
#             id = filename.removesuffix(".json")

#             existing_embeddings = collection.get([id])
#             if len(existing_embeddings["ids"]) > 0:
#                 continue

#             print("Adding new memory to index - " + filename + "...")
#             with open(log_path, "r") as f:
#                 message = json.load(f)

#             message["file"] = id

#             if include_speakers is not None and "speaker" in message:
#                 if message["speaker"] not in include_speakers:
#                     continue

#             message, modified = self.add_message_to_collection(collection, message, include_document=include_documents)

#             if modified == True:
#                 with open(log_path, "w") as f:
#                     json.dump(message, f)

#         if persist:
#             self.chroma_client.persist()

#     def build_index_from_logs(
#         self, rebuild_index: bool = False, include_documents=False, include_speakers: list = None
#     ):
#         if rebuild_index == True:
#             self.chroma_client.delete_collection("chats")
#         collection = self.chroma_client.get_or_create_collection("chats")

#         log_paths = interfaces.logger.list_log_paths()

#         for log_path in log_paths:
#             filename = os.path.basename(log_path)
#             id = filename.removesuffix(".json")

#             existing_embeddings = collection.get([id])
#             if len(existing_embeddings["ids"]) > 0:
#                 continue

#             print("Adding new memory to index - " + filename + "...")
#             with open(log_path, "r") as f:
#                 message = json.load(f)

#             message["file"] = id

#             if include_speakers is not None and "speaker" in message:
#                 if message["speaker"] not in include_speakers:
#                     continue

#             message, modified = self.add_message_to_collection(collection, message, include_document=include_documents)

#             if modified == True:
#                 with open(log_path, "w") as f:
#                     json.dump(message, f)

#         self.chroma_client.persist()

#         # return result

#     def split_into_parts(self, text: str):
#         parts = text.split("\n")
#         return parts


# # load_memory(rebuild_index=False)
# # items = list_memory(k=50)

# # simple console loop to query sentence embeddings loaded into vector database
# # run_console_query_db()

# # load_messages_into_vector_db("memory/extract/summary-0002", "extracts", persist=False)
# # load_messages_into_vector_db("memory/extract/facts", "facts", persist=True)

# # while True:
# #     text = input(": ")
# #     results = memory.query_vector_db(text, num_results=8, collection_name="facts")
# #     for result in results:
# #         print(result["text"])
