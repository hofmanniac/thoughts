import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import uuid
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from thoughts.engine import Context
import logging, warnings
from typing import List

from thoughts.operations.prompting import ContextItemAppender, PromptRunner, PromptStarter

# from thoughts.interfaces.messaging import PromptMessage

class Thought:

    def __init__(self, content: str, embedding = None, id=None, children_ids=None):

        self.content: str = content
        self.embedding = embedding
        self.id = id if id else str(uuid.uuid4())
        self.children: List[Thought] = []  # For runtime usage
        self.children_ids = children_ids if children_ids else []
        # self.max_children = 4

    def add_child(self, child):

        self.children.append(child)
        self.children_ids.append(child.id)

    # def update_summary(self):
    #     if not self.children:
    #         return
    #     combined_text = " ".join([child.content for child in self.children if child.content])
    #     combined_embeddings = np.mean([child.embedding for child in self.children], axis=0)
    #     self.content = combined_text
    #     self.embedding = combined_embeddings

    @classmethod
    def from_dict(cls, data):

        node = cls(np.array(data["embedding"]), data["content"], data["id"], data["children_ids"])
        return node

class SemanticMemoryTree:

    def __init__(self, 
                 context, db_path="memory/semantic", similarity_threshold=0.7, max_cluster_size=4, scaling_factor=10, penalty_coefficient=0.05):
        
        self.context = context
        self.db_path = db_path
        self.similarity_threshold = similarity_threshold
        self.max_cluster_size = max_cluster_size
        self.scaling_factor = scaling_factor
        self.penalty_coefficient = penalty_coefficient

        warnings.filterwarnings("ignore")
        logging.basicConfig(level=logging.CRITICAL)
        self.chroma_client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.chroma_client.get_or_create_collection(name="semantic_memory_tree")
        self.embedder = embedding_functions.DefaultEmbeddingFunction()

        # see thought
        self.root = Thought(content="", id="0")
        self.save_memory(self.root)

    def add_memory(self, memory: Thought):

        if memory.embedding is None:
            embeddings = self.embedder.embed_with_retries([memory.content])
            memory.embedding = embeddings[0]
        self._add_memory_recursive(self.root, memory, depth=0)

    def _add_memory_recursive(self, node: Thought, memory: Thought, depth: int):

        # Step 1: Check if node can directly add the new memory
        # if not node.children or len(node.children) < self.max_cluster_size:
        if not node.children:
            node.add_child(memory)
            print(f"Added {memory.id} to {node.id}")
            self.save_memory(memory)
            self._adjust_clusters(node)
            return

        # Step 2: Calculate similarities between the new memory and the existing children
        child_embeddings = [child.embedding for child in node.children]
        similarities = cosine_similarity([memory.embedding], child_embeddings)

        # Step 3: Adjust similarities based on depth
        adjusted_similarities = similarities[0] - (depth * self.penalty_coefficient)
        max_adjusted_similarity = max(adjusted_similarities)

        # Step 4: Decide to push down or add to current node
        if max_adjusted_similarity > self.similarity_threshold:
            most_similar_child = node.children[np.argmax(adjusted_similarities)]
            self._add_memory_recursive(most_similar_child, memory, depth + 1)
        else:
            node.add_child(memory)
            print(f"Added {memory.id} to {node.id}")
            self.save_memory(memory)
            self._adjust_clusters(node)

    def _summarize_contents(self, contents: list):
        # return "; ".join(contents)
        # instructions = "You are a LLM assistant that creates summaries of memories for a hierarchical semantic database. Summarize the following items into a single paragraph, for use in later retrieval.\Items:\n"
        # instructions = "Summrize the following items in 2-3 concise sentences.'\nItems:\n" # no
        # instructions = "Write a short paragraph that describes the deep assocations between the following items.'\nItems:\n" # no
        # instructions = "Create a single paragraph listing the topics in the items below. Start with 'These items are about'\nItems:\n"
        # instructions = "List all topics and named entities found in the items below.\nItems:\n"
        # instructions = "Extract the common topics from the items below.'\nItems:\n" # too sparse
        instructions = "Create a single paragraph summarizing what the items below are about. Start with 'These items are about'\nItems:\n"

        messages, control = PromptStarter().execute(self.context)
        messages, control = PromptStarter("human", content=instructions).execute(self.context, messages)
        messages, control = ContextItemAppender(items=contents).execute(self.context, messages)
        message, control = PromptRunner(append_history=False).execute(self.context, messages)
        return message.content

    def _adjust_clusters(self, node: Thought):
        
        # Step 1: Check if clustering is needed
        if len(node.children) <= self.max_cluster_size:
            return

        # Step 2: Extract embeddings of children nodes
        embeddings = [child.embedding for child in node.children]

        # Step 3: Determine the number of clusters
        num_clusters = max(2, len(embeddings) // self.scaling_factor)

        # Step 4: Apply KMeans clustering
        kmeans = KMeans(n_clusters=num_clusters)
        clusters = kmeans.fit_predict(embeddings)

        # Step 5: Create new children nodes based on clusters
        new_children = {}
        for i in set(clusters):
            # Get the indices of the children in the current cluster
            cluster_indices = [j for j in range(len(embeddings)) if clusters[j] == i]

            # Concatenate the content of the children in the current cluster
            cluster_contents = [node.children[j].content for j in cluster_indices]
            # combined_content = "; ".join(cluster_contents)
            combined_content = self._summarize_contents(cluster_contents)

            # Get the embeddings of the children in the current cluster
            cluster_embeddings = [embeddings[j] for j in cluster_indices]

            # Calculate the mean embedding for the current cluster
            mean_embedding = np.mean(cluster_embeddings, axis=0)
            # mean_embeddings = self.embedder.embed_with_retries([combined_content])
            # mean_embedding = mean_embeddings[0]

            # Create a new child node for the current cluster
            new_child = Thought(embedding=mean_embedding, content=combined_content)

            # Add the new child node to the dictionary
            new_children[i] = new_child

        # Step 6: Add original children to their respective new cluster nodes
        for i, child in enumerate(node.children):
            cluster_id = clusters[i]
            new_children[cluster_id].add_child(child)
            print(f"Added {child.id} to {new_children[cluster_id].id}")

        # Step 7: Update the children of the current node
        node.children = list(new_children.values())

        # Step 8: Update summaries and save the new children nodes
        # for new_child in node.children:
        #     new_child.update_summary()
        #     self.save_memory(new_child)

        # Step 9: Update the summary of the current node and save it
        # node.update_summary()
        self.save_memory(node)

   
    def save_memory(self, memory: Thought):

        if memory.embedding is None:
            self.collection.upsert(ids=[memory.id], documents=[memory.content])
        else:
            self.collection.upsert(ids=[memory.id], embeddings=[memory.embedding], documents=[memory.content])

    def load_memory(self, memory_id):

        result = self.collection.query(where={"id": memory_id})
        if result:
            return Thought.from_dict(result[0])
        return None

    # utility functions ----------------------------------------------------------------------------

    def load_tree(self):

        # Load all nodes from the collection
        all_nodes = self.collection.query(where={})
        if not all_nodes:
            return

        # Create a dictionary of nodes by ID
        nodes_by_id = {node_data["id"]: Thought.from_dict(node_data) for node_data in all_nodes}

        # Re-establish parent-child relationships
        for node in nodes_by_id.values():
            node.children = [nodes_by_id[child_id] for child_id in node.children_ids if child_id in nodes_by_id]

        # Set the root node
        self.root = nodes_by_id.get(self.root.id)

    def get_memory_summary(self):
        return self._get_memory_summary_recursive(self.root)

    def _get_memory_summary_recursive(self, node: Thought, level = 0):
        result = {"id": node.id, "content": node.content}
        if node.children:
            summaries = [self._get_memory_summary_recursive(child, level + 1) for child in node.children]
            result["children"] = summaries
        # return text + "}\n"
        return result
    
    def reset(self):
        for collection in self.chroma_client.list_collections():
            self.chroma_client.delete_collection(collection.name)
    
        self.collection = self.chroma_client.get_or_create_collection(name="semantic_memory_tree")
        self.root = Thought(content="", id="0")  # Assuming 300-dimensional embeddings
        self.save_memory(self.root)
        
        print("Reset.")


# Thought:

    # def to_dict(self):
    #     return {
    #         "id": self.id,
    #         "embedding": self.embedding.tolist(),
    #         "content": self.content,
    #         "children_ids": self.children_ids
    #     }