from collections import defaultdict
import json
from colorama import Back, Fore, Style
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import uuid
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from thoughts.engine import Context, PipelineExecutor
import logging, warnings
from typing import List
from thoughts.operations.prompting import ContextItemAppender, IncludeContext, PromptRunner, Role
import spacy
from spacy.cli import download
from spacy.util import is_package
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import numpy as np

class Thought:

    def __init__(self, content: str = "", embedding = None, id=None, children_ids=None, is_cluster = False):

        self.content: str = content
        self.embedding = embedding
        self.id: str = str(id) if id else str(uuid.uuid4())
        self.children: List[Thought] = []  # For runtime usage
        self.children_ids = children_ids if children_ids else []
        self.metadata = {}
        self.is_cluster = is_cluster
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

class SemanticClusters:

    def __init__(self, context: Context, recluster: bool = True, hierarchical = False, embed_based_on: str = "mean", delay_clustering=False):

        self.context = context
        self.collection_name = "clusters"
        self.db_path = "memory/clusters"
        self.clusters: List[Thought] = []
        self.memories: List[Thought] = []
        self.similarity_threshold = 0.5 #0.8
        self.max_cluster_size = 6 #10 #4
        self.scaling_factor = 10
        self.recluster = recluster
        self.hierarchical = hierarchical
        self.reduce_dimensionality_when_clustering = True
        self.embed_based_on = embed_based_on
        self.delay_clustering = delay_clustering

        # Load the spaCy model
        model_name = "en_core_web_sm"
        if not is_package(model_name):
            download(model_name)
        self.nlp = spacy.load(model_name)

        warnings.filterwarnings("ignore")
        logging.basicConfig(level=logging.CRITICAL)
        self.chroma_client = chromadb.PersistentClient(path=self.db_path)
        self.memories_db = self.chroma_client.get_or_create_collection(name="memories")
        self.clusters_db = self.chroma_client.get_or_create_collection(name="clusters")
        self.associations_db = self.chroma_client.get_or_create_collection(name="associations")
        self.embedder = embedding_functions.DefaultEmbeddingFunction()

    def trace(self, *args):
        # Convert all arguments to string and join them with a space
        message = ' '.join(map(str, args))
        print(message)


    def verify_embedding(self, thought: Thought):
        if thought.embedding is None:
            embeddings = self.embedder.embed_with_retries([thought.content])
            thought.embedding = embeddings[0]

    def add_cluster(self, cluster: Thought):

        self.trace("ADD CLUSTER:", cluster.content)

        self.verify_embedding(cluster)
    
        cluster.is_cluster = True
        cluster.metadata = {"is_cluster": True}
        self.clusters.append(cluster)
        self.persist_cluster(cluster)

    def associate(self, cluster: Thought, memory: Thought, similarity):
        cluster.add_child(memory)
        self.persist_association(memory, cluster, similarity)

    def add_memory(self, memory: Thought):

        self.trace("ADD MEMORY: ", memory.content)
              
        self.verify_embedding(memory)
        self.persist_memory(memory)

        self.memories.append(memory)

        if self.delay_clustering == False:
            self.cluster_memories()

        # if len(self.clusters) == 0:
        #     cluster = Thought()
        #     self.add_cluster(cluster)
        #     self.associate(cluster, memory, 1.0)
        #     return
        
        # clusters_matches = self.match_to_clusters(memory, self.clusters)
        # for cluster_match in clusters_matches:
        #     cluster: Thought = cluster_match["cluster"]
        #     similarity = cluster_match["similarity"]
        #     self.associate(cluster, memory, similarity)
        #     self.adjust_cluster(cluster)

    def cluster_memories(self):
        
        n_clusters = max(1, len(self.memories) // 5)

        # Extract the embeddings from the Thought objects in memories
        embeddings = np.array([thought.embedding for thought in self.memories])

        # Use KMeans to determine the clusters
        kmeans = KMeans(n_clusters=n_clusters)

        if self.reduce_dimensionality_when_clustering:
            n_components = min(len(embeddings), 50)
            pca = PCA(n_components=min(len(embeddings[0]), n_components))
            reduced_embeddings = pca.fit_transform(embeddings)
            cluster_map = kmeans.fit_predict(reduced_embeddings)
        else:
            cluster_map = kmeans.fit_predict(embeddings)

        # Clear out the current clusters
        self.clusters = []

        # Assign memories to clusters based on the KMeans result
        for cluster_id in range(n_clusters):
            cluster_indices = np.where(cluster_map == cluster_id)[0]
            cluster_embeddings = embeddings[cluster_indices]

            # Create a new Thought object for the cluster centroid
            cluster_centroid = np.mean(cluster_embeddings, axis=0)
            cluster_thought = Thought(embedding=cluster_centroid)

            # Add the original thoughts in this cluster as children to the cluster thought
            for index in cluster_indices:
                cluster_thought.children.append(self.memories[index])

            cluster_thought.content = self._summarize_content(cluster_thought)
            cluster_thought = self.embed_cluster(cluster_thought)

            # Add the cluster thought to the clusters list
            self.add_cluster(cluster_thought)

    def adjust_cluster(self, cluster: Thought):

        if self.recluster == False:
            return
        
        clusters = self.determine_new_clusters(cluster)
        if not clusters:
            return
        
        # clusters = self.set_cluster_contents(clusters)
        # clusters = self.set_cluster_embeddings(clusters)
        if self.hierarchical:
            cluster = self.replace_cluster(cluster, clusters)
        else:
            dummy = list(map(self.add_cluster, clusters))
            self.clusters.remove(cluster)

    def embed_cluster(self, cluster: Thought):
        if self.embed_based_on == "content":
            self.verify_embedding(cluster)
        elif self.embed_based_on == "mean":
            cluster.embedding = np.mean([child.embedding for child in cluster.children], axis=0)
        return cluster

    def replace_cluster(self, cluster: Thought, new_clusters: list):
        if not new_clusters:
            return cluster
        
        new_cluster = Thought(embedding=None)
        new_cluster.children = new_clusters

        new_cluster.content = self._summarize_content(new_cluster)
        new_cluster = self.embed_cluster(new_cluster)

        return new_cluster

    def set_cluster_embeddings(self, clusters: list):
        if not clusters:
            return None
        clusters = list(map(self.embed_cluster, clusters))
        return clusters

    def set_cluster_contents(self, clusters: list):
        if not clusters:
            return None
        clusters = list(map(self._summarize_content, clusters))
        return clusters

    def visualize_clusters(self):
        # Combine all cluster centroids and memory embeddings into a single array
        all_embeddings = []
        cluster_labels = []

        for cluster_id, cluster in enumerate(self.clusters):
            # Add the cluster centroid
            all_embeddings.append(cluster.embedding)
            cluster_labels.append(f"Cluster {cluster_id + 1} Centroid")

            # Add the children (memories in this cluster)
            for child in cluster.children:
                all_embeddings.append(child.embedding)
                cluster_labels.append(f"Cluster {cluster_id + 1} Memory")

        all_embeddings = np.array(all_embeddings)

        # Reduce the dimensionality for visualization (e.g., PCA or t-SNE)
        if len(all_embeddings[0]) > 2:
            reduced_embeddings = PCA(n_components=2).fit_transform(all_embeddings)
        else:
            reduced_embeddings = all_embeddings  # If already 2D

        # Plot the results
        plt.figure(figsize=(10, 8))
        
        added_labels = set()  # Track which labels have been added

        # Plot the cluster centroids
        for i, (x, y) in enumerate(reduced_embeddings):
            label = cluster_labels[i]
            if "Centroid" in label:
                if label not in added_labels:
                    plt.scatter(x, y, color='red', marker='x', s=200, label=label)
                    added_labels.add(label)
                else:
                    plt.scatter(x, y, color='red', marker='x', s=200)
            else:
                plt.scatter(x, y, color='blue', marker='o', s=50)

            # Annotate points with cluster labels
            plt.text(x, y, label, fontsize=9, ha='right')

        plt.title('Visualization of Thought Clusters')
        plt.xlabel('Component 1')
        plt.ylabel('Component 2')
        plt.legend()
        plt.show()

    # def determine_new_clusters(self, cluster: Thought, scaling_factor: int = None):
    #     # If the current cluster already has fewer or equal children than max_cluster_size, return None
    #     if len(cluster.children) <= self.max_cluster_size:
    #         return None

    #     if not scaling_factor:
    #         scaling_factor = self.scaling_factor

    #     embeddings = [child.embedding for child in cluster.children]
    #     num_clusters = max(2, len(embeddings) // scaling_factor)    
    #     kmeans = KMeans(n_clusters=num_clusters)
        
    #     # Dimensionality reduction if required
    #     if self.reduce_dimensionality_when_clustering:
    #         n_components = min(len(embeddings), 50)
    #         pca = PCA(n_components=min(len(embeddings[0]), n_components))
    #         reduced_embeddings = pca.fit_transform(embeddings)
    #         cluster_map = kmeans.fit_predict(reduced_embeddings)
    #     else:
    #         cluster_map = kmeans.fit_predict(embeddings)

    #     if cluster_map is None:
    #         return
        
    #     # Create new clusters based on the cluster_map
    #     new_clusters = defaultdict(list)
    #     for i, child in enumerate(cluster.children):
    #         new_clusters[cluster_map[i]].append(child)
        
    #     # Ensure no cluster exceeds max_cluster_size
    #     result_clusters = []
    #     for children in new_clusters.values():
    #         if len(children) > self.max_cluster_size:
    #             # Re-cluster the children within this cluster to avoid exceeding max_cluster_size
    #             sub_embeddings = [child.embedding for child in children]
    #             sub_num_clusters = max(2, len(sub_embeddings) // self.max_cluster_size)
    #             sub_kmeans = KMeans(n_clusters=sub_num_clusters)
    #             sub_cluster_map = sub_kmeans.fit_predict(sub_embeddings)

    #             sub_clusters = defaultdict(list)
    #             for i, child in enumerate(children):
    #                 sub_clusters[sub_cluster_map[i]].append(child)

    #             for sub_children in sub_clusters.values():
    #                 new_cluster = Thought(embedding=None)
    #                 new_cluster.children = sub_children
    #                 new_cluster.content = self._summarize_content(new_cluster)
    #                 new_cluster = self.embed_cluster(new_cluster)
    #                 result_clusters.append(new_cluster)
    #         else:
    #             new_cluster = Thought(embedding=None)  # Create a new Thought object
    #             new_cluster.children = children  # Assign the children to the new cluster
    #             new_cluster.content = self._summarize_content(new_cluster)
    #             new_cluster = self.embed_cluster(new_cluster)
    #             result_clusters.append(new_cluster)

    #     return result_clusters


    def determine_new_clusters(self, cluster: Thought, scaling_factor: int = None):

        if len(cluster.children) <= self.max_cluster_size:
            return None

        if not scaling_factor:
            scaling_factor = self.scaling_factor

        embeddings = [child.embedding for child in cluster.children]
        num_clusters = max(2, len(embeddings) // scaling_factor)    
        kmeans = KMeans(n_clusters=num_clusters)
                
        if self.reduce_dimensionality_when_clustering:
            n_components = min(len(embeddings), 50)
            pca = PCA(n_components=min(len(embeddings[0]), n_components))
            reduced_embeddings = pca.fit_transform(embeddings)
            cluster_map = kmeans.fit_predict(reduced_embeddings)
        else:
            cluster_map = kmeans.fit_predict(embeddings)

        if cluster_map is None:
            return
        
        # Create new clusters based on the cluster_map
        new_clusters = defaultdict(list)
        for i, child in enumerate(cluster.children):
            new_clusters[cluster_map[i]].append(child)
        
        # Convert defaultdict to a list of Thought objects (new clusters)
        result_clusters = []
        for children in new_clusters.values():
            new_cluster = Thought(embedding=None)  # Create a new Thought object
            new_cluster.children = children  # Assign the children to the new cluster
            new_cluster.content = self._summarize_content(new_cluster)
            new_cluster = self.embed_cluster(new_cluster)
            result_clusters.append(new_cluster)

        return result_clusters
    
    def _summarize_content(self, cluster: Thought, method: str = "ner-nps"):
        contents = [x.content for x in cluster.children]
        result = self._summarize_contents(contents, method=method)
        return result

    def extract_topics_and_entities(self, texts):
        topics_and_entities = set()
        for doc_text in texts:
            doc = self.nlp(doc_text)
            for entity in doc.ents:
                topics_and_entities.add(entity.text)
        return topics_and_entities

    def extract_noun_phrases(self, texts):
            results = set()
            for doc_text in texts:
                doc = self.nlp(doc_text)
                noun_phrases = [chunk.text for chunk in doc.noun_chunks]
                for np in noun_phrases:
                    results.add(np)
            return results

    def _summarize_contents(self, set_one: list, set_two: list = None, method: str ="nps"):

        if method == "ner":
            ners = self.extract_topics_and_entities(set_one)
            result = ", ".join(ners)
            return result
            
        elif method == "nps":
            nps = self.extract_noun_phrases(set_one)
            result = ", ".join(nps)
            return result
        
        elif method == "ner-nps":
            ners = self.extract_topics_and_entities(set_one)
            nps = self.extract_noun_phrases(set_one)
            combined = ners.union(nps)
            result = ", ".join(combined)
            return result

        elif method == "concatenate":
            return "; ".join(set_one)

        elif method == "prompt-summary":
            instructions = "Why would an item appear in Set One and not Set Two? What makes Set One different from Set Two?\n\n"

            # messages = PipelineExecutor([
            #     PromptStarter(),
            #     PromptStarter("human", content=instructions),
            #     ContextItemAppender(items=set_one, title="Set One"),
            #     ContextItemAppender(items=set_two, title="Set Two"),
            #     PromptRunner(append_history=False)
            # ], self.context).execute()
            # result = messages[0].content

            messages, control = Role().execute(self.context)
            messages, control = Role(role="human", content=instructions).execute(self.context, messages)
            messages, control = ContextItemAppender(items=set_one, title="Set One").execute(self.context, messages)
            messages, control = ContextItemAppender(items=set_two, title="Set Two").execute(self.context, messages)
            message, control = PromptRunner(append_history=False).execute(self.context, messages)
            result = message.content

            messages, control = Role().execute(self.context)
            messages, control = Role(role="human", content="Write a paragraph summarizing what Set One from the description below is about. Only describe what it does include. Begin with the phrase 'Set One is about'. Do not mention 'Set Two'. \n\n" + result).execute(self.context, messages)
            message, control = PromptRunner(append_history=False).execute(self.context, messages)
            result = message.content

            result = str.replace(result, "Set One", "this item")
            result = str.replace(result, "Set Two", "other items")
            result = str.capitalize(result[0]) + result[1:]
            return result
    
    # def _summarize_contents(self, set_one: list, set_two: list):
    #     # return "; ".join(contents)

    #     instructions = "Why would an item appear in Set One and not Set Two? What makes Set One different from Set Two?\n\n"

    #     messages, control = PromptStarter().execute(self.context)
    #     messages, control = PromptStarter("human", content=instructions).execute(self.context, messages)
    #     messages, control = ContextItemAppender(items=set_one, title="Set One").execute(self.context, messages)
    #     messages, control = ContextItemAppender(items=set_two, title="Set Two").execute(self.context, messages)
    #     message, control = PromptRunner(append_history=False).execute(self.context, messages)
    #     result = message.content

    #     messages, control = PromptStarter().execute(self.context)
    #     messages, control = PromptStarter("human", content="Write a paragraph summarizing what Set One from the description below is about. Only describe what it does include. Begin with the phrase 'Set One is about'. Do not mention 'Set Two'. \n\n" + result).execute(self.context, messages)
    #     message, control = PromptRunner(append_history=False).execute(self.context, messages)
    #     result = message.content

    #     result = str.replace(result, "Set One", "this item")
    #     result = str.replace(result, "Set Two", "other items")
    #     result = str.capitalize(result[0]) + result[1:]
    #     return result
    
    def match_to_cluster(self, memory: Thought, cluster: Thought):
        results = []
        similarities = cosine_similarity([memory.embedding], [cluster.embedding])
        closest_similarity = max(similarities)[0]

        # Add any additional logic here
        if closest_similarity > self.similarity_threshold:

            best_cluster = cluster
            best_similarity = closest_similarity

            if self.hierarchical:
                child_matches = self.match_to_clusters(memory, cluster.children)
                if len(child_matches) > 0:
                    best_child_match = max(child_matches, key=lambda x: x["similarity"])
                    best_child_cluster = best_child_match["cluster"]
                    best_child_similarity = best_child_match["similarity"]
                    if best_child_similarity > best_similarity:
                        best_cluster = best_child_cluster
                        best_similarity = best_child_similarity

            results.append({"cluster": best_cluster, "similarity": best_similarity})
        else:
            # print(f'{Fore.RED} - Not Matched:\t {cluster.content[0:40]} {closest_similarity}{Style.RESET_ALL}')
            pass

        return results, closest_similarity

    def match_to_clusters(self, memory: Thought, clusters: List[Thought]) -> List[Thought]:
        if len(clusters) == 0:
            return []
        
        cluster_assignments = []
        best_match: Thought = None
        best_match_similarity = None
        
        cluster: Thought
        for cluster in clusters:

            if cluster.is_cluster == False:
                continue

            cluster_matches, closest_similarity = self.match_to_cluster(memory, cluster)
            cluster_assignments.extend(cluster_matches)

            if best_match_similarity is None:
                best_match_similarity = closest_similarity
                best_match = cluster
            else:
                if closest_similarity > best_match_similarity:
                    best_match_similarity = closest_similarity
                    best_match = cluster

        if len(cluster_assignments) == 0:

            if best_match_similarity and best_match_similarity > 0: # negative is diametrically opposite, zero orthogonal

                best_cluster = best_match
                best_similarity = closest_similarity

                if self.hierarchical:
                    child_matches = self.match_to_clusters(memory, best_cluster.children)
                    if len(child_matches) > 0:
                        best_child_match = max(child_matches, key=lambda x: x["similarity"])
                        best_child_cluster = best_child_match["cluster"]
                        best_child_similarity = best_child_match["similarity"]
                        if best_child_similarity > best_similarity:
                            best_cluster = best_child_cluster
                            best_similarity = best_child_similarity
                        
                cluster_assignments.append({"cluster": best_cluster, "similarity": best_similarity})
                # print(f'{Fore.GREEN} - Best Match:\t {best_match.content[0:40]} {best_match_similarity}{Style.RESET_ALL}')
                # cluster_assignments.append({"cluster": best_match, "similarity": best_match_similarity})

                # child_matches = self.match_to_clusters(memory, best_match.children)
                # if len(child_matches) > 0 and closest_child_similarity > best_match_similarity:
                #     best_child_match = max(child_matches, key=lambda x: x["similarity"])
                #     cluster_assignments.append({"cluster": best_child_match, "similarity": closest_child_similarity})
                # else:
                #     print(f'{Fore.GREEN} - Matched:\t {cluster.content[0:40]} {closest_similarity}{Style.RESET_ALL}')
                #     cluster_assignments.append({"cluster": cluster, "similarity": closest_similarity})

            else:
                print(f' - Matches: {Fore.RED} No Match{Style.RESET_ALL}')

        return cluster_assignments

    def persist_memory(self, memory: Thought):
        pass
        # if not memory.metadata:
        #     self.memories_db.upsert(ids=[memory.id], embeddings=[memory.embedding], documents=[memory.content])
        # else:
        #     self.memories_db.upsert(ids=[memory.id], embeddings=[memory.embedding], documents=[memory.content], metadatas=[memory.metadata])

    def persist_cluster(self, memory: Thought):
        pass
        # self.clusters_db.upsert(ids=[memory.id], embeddings=[memory.embedding], documents=[memory.content], metadatas=[memory.metadata])

    def persist_association(self, memory: Thought, cluster: Thought, similarity):
        pass
        # assocation = {"memory-id": memory.id, "cluster-id": cluster.id, "similarity": similarity}
        # self.associations_db.upsert(
        #     ids=[str(uuid.uuid4())], documents=["memory-cluster"], metadatas=[assocation])

    def reset(self):
        for collection in self.chroma_client.list_collections():
            self.chroma_client.delete_collection(collection.name)
    
        # self.collection = self.chroma_client.get_or_create_collection(name=self.collection_name)
        # self.root = Thought(content="", id="0")
        # self.persist_memory(self.root)
        
        print("Reset.")

    def save_as_json(self, path: str):
        result = self.to_json()
        with open(path, "w") as f:
            json.dump(result, f)

    def to_json(self):
        results = []
        for cluster in self.clusters:
            cluster = self._to_json_recursive(cluster)
            results.append(cluster)
        return results

    def _to_json_recursive(self, node: Thought, level = 0):
        result = {"id": node.id, "content": node.content}
        if node.children:
            summaries = [self._to_json_recursive(child, level + 1) for child in node.children]
            result["children"] = summaries
        # return text + "}\n"
        return result
    
    def consolidate_root(self, scaling_factor: int = 2):
        cluster = Thought()
        cluster.children.extend(self.clusters)
        consolidated_clusters = self._consolidate_clusters(cluster=cluster, scaling_factor=scaling_factor)
        self.clusters = consolidated_clusters

    def consolidate_cluster(self, cluster: Thought, scaling_factor: int = 2):
        self._consolidate_clusters(cluster, scaling_factor=scaling_factor)
        consolidated_clusters = self.determine_new_clusters(cluster, scaling_factor)
        cluster.children = consolidated_clusters

    def _consolidate_clusters(self, cluster: Thought, scaling_factor: int = 2):
        consolidated_clusters = self.determine_new_clusters(cluster, scaling_factor)
        # return consolidated_clusters
        new_clusters = []
        consolidated_cluster: Thought
        for consolidated_cluster in consolidated_clusters:
            new_cluster = Thought()
            for child in consolidated_cluster.children:
                new_cluster.children.extend(child.children)
            new_clusters.append(new_cluster)
        return new_clusters
    
    # # Function to recursively add sub-items as children
    # def add_children_recursively(data, parent: Thought):
    #     for idx, topic in enumerate(data):
    #         memory = Thought(topic["topic"] + ": " + topic["content"], id=parent.id + '.' + str(idx), is_cluster=True)
    #         self.verify_embedding(memory)
    #         parent.add_child(memory)
    #         if "items" in topic:
    #             add_children_recursively(topic["items"], memory)

    # # Function to add top-level topics and their children
    # def add_topics(data):
    #     for idx, topic in enumerate(data):
    #         memory = Thought(topic["topic"] + ": " + topic["content"], id=str(idx))
    #         if "items" in topic:
    #             add_children_recursively(topic["items"], memory)
    #         self.add_cluster(memory)

    def load_clusters(self, file_path):
        with open(file_path, "r") as f:
            test_data = json.load(f)
        idx = 1
        for item in test_data:
            message = Thought(item, id="c-" + str(idx))
            self.add_cluster(message)
            idx += 1

    def load_memories(self, file_path):
        with open(file_path, "r") as f:
            test_data = json.load(f)
        idx = 1
        for item in test_data:
            message = Thought(item, id="m-" + str(idx))
            self.add_memory(message)
            idx += 1

    # def form_cluster_from_items(self, items):
    #     # combined_content = "; ".join(cluster_contents)

    #     # summarize the contents, using another set for comparison
    #     # control_idx = (i + 1) % len(unique_clusters)
    #     # control_indices = [j for j in range(len(embeddings)) if new_clusters[j] == control_idx]
    #     # control_contents = [node.children[j].content for j in control_indices]
    #     # control_content = "; ".join(control_contents)
    #     # cluster_summary = self._summarize_contents(cluster_contents, control_contents)

    #     ners = self.extract_topics_and_entities(items)
    #     cluster_summary = ", ".join(ners)
        
    #     # Calculate the mean embedding for the current cluster
    #     cluster_embeddings = [embeddings[j] for j in cluster_indices]
    #     mean_embedding = np.mean(cluster_embeddings, axis=0)

    #     # calculate new embedding based on the named entity recognition
    #     # mean_embeddings = self.embedder.embed_with_retries([cluster_summary])
    #     # mean_embedding = mean_embeddings[0]

    #     # Create a new child node for the current cluster
    #     new_child = Thought(embedding=mean_embedding, content=cluster_summary, is_cluster=True)
        
    
    # def split_cluster(self, cluster: Thought, new_clusters, embeddings):
    #     if new_clusters is None:
    #         return
        
    #     unique_clusters = list(set(new_clusters))

    #     new_children = {}
    #     for i in unique_clusters:
    #         cluster_indices = [j for j in range(len(embeddings)) if new_clusters[j] == i]

    #         # Concatenate the content of the children in the current cluster
    #         cluster_contents = [cluster.children[j].content for j in cluster_indices]

    #         # combined_content = "; ".join(cluster_contents)

    #         # summarize the contents, using another set for comparison
    #         # control_idx = (i + 1) % len(unique_clusters)
    #         # control_indices = [j for j in range(len(embeddings)) if new_clusters[j] == control_idx]
    #         # control_contents = [node.children[j].content for j in control_indices]
    #         # control_content = "; ".join(control_contents)
    #         # cluster_summary = self._summarize_contents(cluster_contents, control_contents)

    #         ners = self.extract_topics_and_entities(cluster_contents)
    #         cluster_summary = ", ".join(ners)
            
    #         # Calculate the mean embedding for the current cluster
    #         cluster_embeddings = [embeddings[j] for j in cluster_indices]
    #         mean_embedding = np.mean(cluster_embeddings, axis=0)

    #         # calculate new embedding based on the named entity recognition
    #         # mean_embeddings = self.embedder.embed_with_retries([cluster_summary])
    #         # mean_embedding = mean_embeddings[0]

    #         # Create a new child node for the current cluster
    #         new_child = Thought(embedding=mean_embedding, content=cluster_summary, is_cluster=True)

    #         # Add the new child node to the dictionary
    #         new_children[i] = new_child
    #         print("Addding cluster", new_child.id, "Content:", new_child.content)

    #     if self.hierarchical:
    #         # Step 6: Add original children to their respective new cluster nodes
    #         for i, child in enumerate(cluster.children):
    #             cluster_id = new_clusters[i]
    #             new_children[cluster_id].add_child(child)
    #             print(f"Added {child.id} to {new_children[cluster_id].id}")

    #         # Step 7: Update the children of the current node
    #         new_children_list = new_children.values()
    #         cluster.children = list(new_children_list)
    #         print("Split", cluster.id, ", New Children:", ", ".join([x.id for x in cluster.children]))
    #         # Step 8: Update summaries and save the new children nodes
    #         # for new_child in node.children:
    #         #     new_child.update_summary()
    #         #     self.save_memory(new_child)
    #     else:
    #         self.clusters.remove(cluster)
    #         new_child: Thought
    #         for new_child in new_children.values():
    #             self.add_cluster(new_child)

        # Step 9: Update the summary of the current node and save it
        # node.update_summary()
        # self.persist_cluster(node)

# class SemanticMemoryTree:

#     def __init__(self, 
#                  context, db_path="memory/semantic", similarity_threshold=0.7, max_cluster_size=4, scaling_factor=10, penalty_coefficient=0.05):
        
#         self.context = context
#         self.db_path = db_path
#         self.similarity_threshold = similarity_threshold
#         self.max_cluster_size = max_cluster_size
#         self.scaling_factor = scaling_factor
#         self.penalty_coefficient = penalty_coefficient

#         warnings.filterwarnings("ignore")
#         logging.basicConfig(level=logging.CRITICAL)
#         self.chroma_client = chromadb.PersistentClient(path=self.db_path)
#         self.collection = self.chroma_client.get_or_create_collection(name="semantic_memory_tree")
#         self.embedder = embedding_functions.DefaultEmbeddingFunction()

#         # see thought
#         self.root = Thought(content="", id="0")
#         self.save_memory(self.root)

#     def add_memory(self, memory: Thought):

#         if memory.embedding is None:
#             embeddings = self.embedder.embed_with_retries([memory.content])
#             memory.embedding = embeddings[0]
#         self._add_memory_recursive(self.root, memory, depth=0)

#     def _add_memory_recursive(self, node: Thought, memory: Thought, depth: int):

#         # Step 1: Check if node can directly add the new memory
#         # if not node.children or len(node.children) < self.max_cluster_size:
#         if not node.children:
#             node.add_child(memory)
#             print(f"Added {memory.id} to {node.id}")
#             self.save_memory(memory)
#             self._adjust_clusters(node)
#             return

#         # Step 2: Calculate similarities between the new memory and the existing children
#         child_embeddings = [child.embedding for child in node.children]
#         similarities = cosine_similarity([memory.embedding], child_embeddings)

#         # Step 3: Adjust similarities based on depth
#         adjusted_similarities = similarities[0] - (depth * self.penalty_coefficient)
#         max_adjusted_similarity = max(adjusted_similarities)

#         # Step 4: Decide to push down or add to current node
#         if max_adjusted_similarity > self.similarity_threshold:
#             most_similar_child = node.children[np.argmax(adjusted_similarities)]
#             self._add_memory_recursive(most_similar_child, memory, depth + 1)
#         else:
#             node.add_child(memory)
#             print(f"Added {memory.id} to {node.id}")
#             self.save_memory(memory)
#             self._adjust_clusters(node)

#     def _summarize_contents(self, contents: list):
#         # return "; ".join(contents)
#         # instructions = "You are a LLM assistant that creates summaries of memories for a hierarchical semantic database. Summarize the following items into a single paragraph, for use in later retrieval.\Items:\n"
#         # instructions = "Summrize the following items in 2-3 concise sentences.'\nItems:\n" # no
#         # instructions = "Write a short paragraph that describes the deep assocations between the following items.'\nItems:\n" # no
#         # instructions = "Create a single paragraph listing the topics in the items below. Start with 'These items are about'\nItems:\n"
#         # instructions = "List all topics and named entities found in the items below.\nItems:\n"
#         # instructions = "Extract the common topics from the items below.'\nItems:\n" # too sparse
#         instructions = "Create a single paragraph summarizing what the items below are about. Start with 'These items are about'\nItems:\n"

#         messages, control = PromptStarter().execute(self.context)
#         messages, control = PromptStarter("human", content=instructions).execute(self.context, messages)
#         messages, control = ContextItemAppender(items=contents).execute(self.context, messages)
#         message, control = PromptRunner(append_history=False).execute(self.context, messages)
#         return message.content

#     def _adjust_clusters(self, node: Thought):
        
#         # Step 1: Check if clustering is needed
#         if len(node.children) <= self.max_cluster_size:
#             return

#         # Step 2: Extract embeddings of children nodes
#         embeddings = [child.embedding for child in node.children]

#         # Step 3: Determine the number of clusters
#         num_clusters = max(2, len(embeddings) // self.scaling_factor)

#         # Step 4: Apply KMeans clustering
#         kmeans = KMeans(n_clusters=num_clusters)
#         clusters = kmeans.fit_predict(embeddings)

#         # Step 5: Create new children nodes based on clusters
#         new_children = {}
#         for i in set(clusters):
#             # Get the indices of the children in the current cluster
#             cluster_indices = [j for j in range(len(embeddings)) if clusters[j] == i]

#             # Concatenate the content of the children in the current cluster
#             cluster_contents = [node.children[j].content for j in cluster_indices]
#             # combined_content = "; ".join(cluster_contents)
#             combined_content = self._summarize_contents(cluster_contents)

#             # Get the embeddings of the children in the current cluster
#             cluster_embeddings = [embeddings[j] for j in cluster_indices]

#             # Calculate the mean embedding for the current cluster
#             mean_embedding = np.mean(cluster_embeddings, axis=0)
#             # mean_embeddings = self.embedder.embed_with_retries([combined_content])
#             # mean_embedding = mean_embeddings[0]

#             # Create a new child node for the current cluster
#             new_child = Thought(embedding=mean_embedding, content=combined_content)

#             # Add the new child node to the dictionary
#             new_children[i] = new_child

#         # Step 6: Add original children to their respective new cluster nodes
#         for i, child in enumerate(node.children):
#             cluster_id = clusters[i]
#             new_children[cluster_id].add_child(child)
#             print(f"Added {child.id} to {new_children[cluster_id].id}")

#         # Step 7: Update the children of the current node
#         node.children = list(new_children.values())

#         # Step 8: Update summaries and save the new children nodes
#         # for new_child in node.children:
#         #     new_child.update_summary()
#         #     self.save_memory(new_child)

#         # Step 9: Update the summary of the current node and save it
#         # node.update_summary()
#         self.save_memory(node)

#     def save_memory(self, memory: Thought):

#         if memory.embedding is None:
#             self.collection.upsert(ids=[memory.id], documents=[memory.content])
#         else:
#             self.collection.upsert(ids=[memory.id], embeddings=[memory.embedding], documents=[memory.content])

#     def load_memory(self, memory_id):

#         result = self.collection.query(where={"id": memory_id})
#         if result:
#             return Thought.from_dict(result[0])
#         return None

#     # utility functions ----------------------------------------------------------------------------

#     def load_tree(self):

#         # Load all nodes from the collection
#         all_nodes = self.collection.query(where={})
#         if not all_nodes:
#             return

#         # Create a dictionary of nodes by ID
#         nodes_by_id = {node_data["id"]: Thought.from_dict(node_data) for node_data in all_nodes}

#         # Re-establish parent-child relationships
#         for node in nodes_by_id.values():
#             node.children = [nodes_by_id[child_id] for child_id in node.children_ids if child_id in nodes_by_id]

#         # Set the root node
#         self.root = nodes_by_id.get(self.root.id)

#     def get_memory_summary(self):
#         return self._get_memory_summary_recursive(self.root)

#     def _get_memory_summary_recursive(self, node: Thought, level = 0):
#         result = {"id": node.id, "content": node.content}
#         if node.children:
#             summaries = [self._get_memory_summary_recursive(child, level + 1) for child in node.children]
#             result["children"] = summaries
#         # return text + "}\n"
#         return result
    
#     def reset(self):
#         for collection in self.chroma_client.list_collections():
#             self.chroma_client.delete_collection(collection.name)
    
#         self.collection = self.chroma_client.get_or_create_collection(name="semantic_memory_tree")
#         self.root = Thought(content="", id="0")  # Assuming 300-dimensional embeddings
#         self.save_memory(self.root)
        
#         print("Reset.")