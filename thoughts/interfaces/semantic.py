import json
from math import ceil, sqrt
from matplotlib import pyplot as plt
import networkx as nx
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity
from pyvis.network import Network
from chromadb.utils import embedding_functions

class SemanticNode:
    def __init__(self, text, embedding = None):
        # self.id: str = str(id) if id else str(uuid.uuid4())
        self.text = text
        self.embedding = embedding

class SemanticMemory:
    def __init__(self, allow_multiple = False, similarity_threshold=0.8):
        self.graph = nx.Graph()
        self.memory_counter = 0
        self.cluster_labels = None
        self.embedder = embedding_functions.DefaultEmbeddingFunction()
        self.allow_multiple = allow_multiple
        self.similarity_threshold = similarity_threshold
        self.rebuild_every = 5
        self.items_since_last_rebuild = 0

    def clear_all(self):
        self.graph = nx.Graph()
        self.memory_counter = 0
        self.cluster_labels = None
        self.items_since_last_rebuild = 0

    def generate_embedding(self, text):
        """
        Generate an embedding for the given sentence using SentenceTransformers.
        """
        embeddings = self.embedder.embed_with_retries([text])
        return embeddings[0]
    
    def add_memory(self, semantic_node: SemanticNode):
        """
        Add a memory to the graph with its associated SemanticNode.
        """
        node_id = self.memory_counter

        if not semantic_node.embedding:
            embedding = self.generate_embedding(semantic_node.text)
            semantic_node.embedding = embedding

        self.graph.add_node(node_id, semantic_node=semantic_node)
        
        self.memory_counter += 1
        self.items_since_last_rebuild += 1

        if self.items_since_last_rebuild >= self.rebuild_every:
            self.rebuild_clusters()
            self.items_since_last_rebuild = 0
        else:
            # Optionally associate with existing clusters in real-time
            self._associate_with_clusters(node_id, embedding)

    def _associate_with_clusters(self, node_id, embedding):
        """
        Associate a new memory with existing clusters.
        
        Parameters:
        - allow: str, 'closest' to associate with the closest cluster, or 'all' to associate with all clusters
        that pass a similarity threshold.
        - similarity_threshold: float, the minimum similarity score required to associate with a cluster 
        when mode is 'all'. Only used if mode is 'all'.
        """
        if self.cluster_labels is not None:
            if self.allow_multiple == False:
                closest_cluster, similarity = self._find_closest_cluster(embedding)
                self.graph.nodes[node_id]['cluster'] = closest_cluster
                self._link_to_cluster_centroid(node_id, closest_cluster)
            
            elif self.allow_multiple == True:
                associated_clusters = []
                for cluster_label, similarity in self._find_all_clusters_above_threshold(embedding):
                    self.graph.nodes[node_id].setdefault('clusters', []).append(cluster_label)
                    self._link_to_cluster_centroid(node_id, cluster_label)
                    associated_clusters.append(cluster_label)
                
                if not associated_clusters:
                    # No clusters above threshold, fall back to closest cluster
                    closest_cluster, similarity = self._find_closest_cluster(embedding)
                    self.graph.nodes[node_id]['cluster'] = closest_cluster
                    self._link_to_cluster_centroid(node_id, closest_cluster)
                    print(f"No clusters above similarity threshold. Associated with the closest cluster: {closest_cluster}.")

    def _find_all_clusters_above_threshold(self, embedding):
        """
        Find all clusters with a similarity above a specified threshold.
        
        Returns:
        - List of tuples (cluster_label, similarity) for all clusters that meet or exceed the threshold.
        """
        matching_clusters = []
        
        for node_id, data in self.graph.nodes(data=True):
            if'centroid'in data:  # Centroid nodes are marked with this attribute
                centroid_embedding = data['semantic_node'].embedding
                similarity = cosine_similarity([embedding], [centroid_embedding])[0][0]
                if similarity >= self.similarity_threshold:
                    matching_clusters.append((data['cluster'], similarity))
        
        return matching_clusters

    def _find_closest_cluster(self, embedding):
        """
        Find the closest existing cluster to the new memory.
        """
        max_similarity = -1
        closest_cluster = None

        for node_id, data in self.graph.nodes(data=True):
            if 'centroid' in data:  # Centroid nodes are marked with this attribute
                centroid_embedding = data['semantic_node'].embedding
                similarity = cosine_similarity([embedding], [centroid_embedding])[0][0]
                if similarity > max_similarity:
                    max_similarity = similarity
                    closest_cluster = data['cluster']

        return closest_cluster, max_similarity

    def _link_to_cluster_centroid(self, node_id, cluster_label):
        """
        Create an edge between the new memory and the centroid of its assigned cluster.
        """
        for centroid_node, data in self.graph.nodes(data=True):
            if data.get('cluster') == cluster_label and 'centroid' in data:
                self.graph.add_edge(node_id, centroid_node)
                break

    def rebuild_clusters(self, n_clusters=None, max_nodes_per_cluster=None):
        """
        Rebuild clusters for all memories in the graph.
        """

        if not n_clusters:
            if max_nodes_per_cluster:
                num_nodes = self.graph.number_of_nodes()
                n_clusters = ceil(num_nodes / max_nodes_per_cluster)
            else:
                n_clusters = self.find_optimal_clusters_silhouette()

        embeddings = []
        node_ids = []

        for node_id, data in self.graph.nodes(data=True):
            embeddings.append(data['semantic_node'].embedding)
            node_ids.append(node_id)

        # Apply KMeans clustering
        kmeans = KMeans(n_clusters=n_clusters)
        self.cluster_labels = kmeans.fit_predict(embeddings)

        # Update graph with new clusters
        for node_id, cluster_label in zip(node_ids, self.cluster_labels):
            self.graph.nodes[node_id]['cluster'] = cluster_label

        # Optionally, designate cluster centroids
        self._update_centroids(kmeans.cluster_centers_)

    def _update_centroids(self, centroids):
        """
        Update the graph to include centroid nodes for each cluster.
        """
        # First, remove old centroids
        for node_id, data in list(self.graph.nodes(data=True)):
            if 'centroid' in data:
                self.graph.remove_node(node_id)

        # Add new centroid nodes
        for i, centroid in enumerate(centroids):
            centroid_node_id = f'centroid_{i}'
            semantic_node = SemanticNode(None, centroid)  # Centroids may not have an associated sentence
            self.graph.add_node(centroid_node_id, semantic_node=semantic_node, cluster=i, centroid=True)
            # Optionally, link centroid to all nodes in its cluster
            for node_id, data in self.graph.nodes(data=True):
                if data.get('cluster') == i and not data.get('centroid'):
                    self.graph.add_edge(centroid_node_id, node_id)

    def get_cluster(self, cluster_label):
        """
        Retrieve all sentences in a specific cluster.
        """
        return [data['semantic_node'].text for node_id, data in self.graph.nodes(data=True) if data.get('cluster') == cluster_label]

    def find_similar_memories(self, target_embedding, threshold=0.8):
        """
        Find memories that are semantically similar to the given embedding.
        """
        similar_nodes = []
        for node_id, data in self.graph.nodes(data=True):
            embedding = data['semantic_node'].embedding
            if embedding is not None:
                similarity = cosine_similarity([target_embedding], [embedding])[0][0]
                if similarity >= threshold:
                    similar_nodes.append(data['semantic_node'].text)
        return similar_nodes
    
    def find_optimal_clusters_silhouette(self, max_k=None):
        """
        Determine the optimal number of clusters using the Silhouette Score.
        """
        num_nodes = self.graph.number_of_nodes()
        if num_nodes < 2:
            print("Not enough memories to form clusters.")
            return None
        
        embeddings = [data['semantic_node'].embedding for _, data in self.graph.nodes(data=True)]
        silhouette_scores = []

        if not max_k:
            max_k = min(int(sqrt(num_nodes)), num_nodes)  # Square root heuristic
            
        for k in range(2, max_k + 1):
            kmeans = KMeans(n_clusters=k)
            labels = kmeans.fit_predict(embeddings)
            score = silhouette_score(embeddings, labels)
            silhouette_scores.append(score)

        # Plot silhouette scores
        # plt.figure(figsize=(8, 5))
        # plt.plot(range(2, max_k + 1), silhouette_scores, 'bo-')
        # plt.xlabel('Number of clusters (k)')
        # plt.ylabel('Silhouette Score')
        # plt.title('Silhouette Score For Optimal k')
        # plt.show()

        optimal_k = range(2, max_k + 1)[silhouette_scores.index(max(silhouette_scores))]
        print(f"Optimal number of clusters: {optimal_k}")
        return optimal_k
    
    def visualize_graph_interactive(self, file_name="semantic_memory_graph.html"):
        """
        Visualize the graph interactively using Pyvis.
        """
        net = Network(notebook=True, height="750px", width="100%", bgcolor="#222222", font_color="white")

        for node_id, data_dict in self.graph.nodes(data=True):
            semantic_node = data_dict['semantic_node']
            label = semantic_node.text[:30] + '...' if semantic_node.text else "Centroid"
            color = 'red' if data_dict.get('centroid', False) else 'blue'
            net.add_node(node_id, label=label, color=color, title=semantic_node.text)

        for source, target in self.graph.edges():
            net.add_edge(source, target)

        net.show(file_name)

    # def generate_pyvis_graph(self):
    #     """
    #     Generate the Pyvis graph and return it as HTML.
    #     """
    #     net = Network(notebook=True, neighborhood_highlight=True,
    #                   height="500px", width="100%", bgcolor="#222222", font_color="white")

    #     for node_id, data_dict in self.graph.nodes(data=True):
    #         semantic_node = data_dict['semantic_node']
    #         label = semantic_node.text[:30] + '...' if semantic_node.text else "Centroid"
    #         color = 'red' if data_dict.get('centroid', False) else 'blue'
    #         net.add_node(node_id, label=label, color=color, title=semantic_node.text)

    #     for source, target in self.graph.edges():
    #         net.add_edge(source, target)

    #     # Generate HTML file content
    #     return net.generate_html()
    
    # def plot_networkx_graph(self):
    #     """
    #     Plot the graph using NetworkX and Matplotlib.
    #     """
    #     plt.figure(figsize=(12, 12))
    #     pos = nx.spring_layout(self.graph)  # positions for all nodes

    #     # nodes
    #     nx.draw_networkx_nodes(self.graph, pos, node_size=700, node_color="blue")

    #     # edges
    #     nx.draw_networkx_edges(self.graph, pos, width=2)

    #     # labels
    #     labels = {node_id: data['semantic_node'].sentence[:20] + '...' for node_id, data in self.graph.nodes(data=True)}
    #     nx.draw_networkx_labels(self.graph, pos, labels, font_size=12)

    #     plt.title("Semantic Memory Graph")
    #     st.pyplot(plt)  # Render the plot in Streamlit
    #     return plt
        
    def load_memories(self, file_path):
        with open(file_path, "r") as f:
            test_data = json.load(f)
        for item in test_data:
            message = SemanticNode(text=item)
            self.add_memory(message)