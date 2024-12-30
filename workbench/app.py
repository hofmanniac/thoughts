import json
import os
import random
import sys

from matplotlib import pyplot as plt

from thoughts.interfaces.semantic import SemanticNode
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from time import sleep
import streamlit as st

from thoughts.agents.chat import ChatAgent
from thoughts.engine import Context
from thoughts.interfaces.messaging import HumanMessage
import streamlit.components.v1 as components
import networkx as nx
from pyvis.network import Network

def generate_networkx_graph(graph):
    """
    Generate the NetworkX graph and plot it using Matplotlib.
    """
    plt.figure(figsize=(12, 12))
    
    # Create positions for each node
    pos = nx.spring_layout(graph)  # Spring layout for a nice distribution
    
    # Create lists for node colors and labels
    node_colors = []
    node_labels = {}
    
    for node_id, data_dict in graph.nodes(data=True):
        semantic_node = data_dict['semantic_node']
        label = semantic_node.text[:30] + '...' if semantic_node.text else "Centroid"
        node_labels[node_id] = label
        color = 'red' if data_dict.get('centroid', False) else 'blue'
        node_colors.append(color)
    
    # Draw the nodes with their labels and colors
    nx.draw_networkx_nodes(graph, pos, node_color=node_colors, node_size=700)
    nx.draw_networkx_labels(graph, pos, labels=node_labels, font_size=12, font_color='white')
    
    # Draw the edges
    nx.draw_networkx_edges(graph, pos, edge_color='white', width=2)
    
    # Set the background color
    plt.gca().set_facecolor('#222222')
    
    # Display the plot
    plt.title("Semantic Memory Graph", fontsize=16, color='white')
    # plt.show()
    st.pyplot(plt)  # Render the plot in Streamlit

def generate_pyvis_graph(graph):
    """
    Generate the Pyvis graph and return it as HTML.
    """
    net = Network(notebook=True, neighborhood_highlight=True,
                    height="600px", width="100%", bgcolor="#222222", font_color="white")

    for node_id, data_dict in graph.nodes(data=True):
        semantic_node = data_dict['semantic_node']
        label = semantic_node.text[:30] + '...' if semantic_node.text else "Centroid"
        color = 'red' if data_dict.get('centroid', False) else 'blue'
        net.add_node(node_id, label=label, color=color, title=semantic_node.text)

    for source, target in graph.edges():
        net.add_edge(source, target)

    # Customize physics settings for the network
    physics_options = {
        "physics": {
            "enabled": True,
            "barnesHut": {
                "gravitationalConstant": -2000,
                "centralGravity": 0.3,
                "springLength": 100,
                "springConstant": 0.04,
                "damping": 0.09,
                "avoidOverlap": 0.5
            },
            "minVelocity": 0.75,
            "solver": "barnesHut"
        }
    }
    
    net.set_options(json.dumps(physics_options))

    # Generate HTML file content
    return net.generate_html()

def semantic_memory():

    from thoughts.interfaces.semantic import SemanticMemory

    st.set_page_config(layout="wide")

    # context = Context(session_id="semantic-clusters", persist_session=False)
    # Initialize SemanticMemory in session_state
    if 'semantic_memory' not in st.session_state:
        st.session_state.semantic_memory = SemanticMemory()
    semantic_memory = st.session_state.semantic_memory
    
    # Streamlit interface
    st.title("Semantic Memory Graph")

    left_column, right_column = st.columns(2)

    with left_column:

        # Button to load memories from a file
        data_source = st.selectbox("Load memories", ["history-items", "personal-items", "general-items", "physics-items"])

        if st.button("Clear All"):
            semantic_memory.clear_all()

        if st.button("Load Memories from File"):
            # Assuming you have a file path or method to get the file path
            # semantic_memory.load_clusters("samples/data/history-topics.json")
            # semantic_memory.load_memories("samples/data/history-items.json")
            # semantic_memory.load_memories("samples/data/personal-items.json")
            # semantic_memory.load_memories("samples/data/physics-items.json")
            semantic_memory.load_memories(f"samples/data/{data_source}.json")
            semantic_memory.rebuild_clusters(max_nodes_per_cluster=10)
            
            st.success(f"Loaded memories")

        if "memory_text" not in st.session_state:
            st.session_state.memory_text = ""
        def submit():
            st.session_state.memory_text = st.session_state.ctl_memory_text
            st.session_state.ctl_memory_text = ""
            semantic_node = SemanticNode(text=st.session_state.memory_text)
            semantic_memory.add_memory(semantic_node)
        st.text_input("Enter text here", key="ctl_memory_text", on_change=submit)
        memory_text = st.session_state.memory_text
        st.success(memory_text)

    with right_column:
        # Choose the rendering method
        render_method = st.selectbox("Choose the rendering method", ["Pyvis", "NetworkX with Matplotlib"])

        # Re-render the graph based on the selected method
        if render_method == "Pyvis":
            graph_html = generate_pyvis_graph(semantic_memory.graph)
            components.html(graph_html, height=610)
        elif render_method == "NetworkX with Matplotlib":
            generate_networkx_graph(semantic_memory.graph)

def main():

    agent1_context = Context(content_path="chat")
    agent1 = ChatAgent(context=agent1_context, prompt_name="chat-continue", handle_io=False)

    agent2_context = Context(content_path="prompts")
    agent2 = ChatAgent(context=agent2_context, prompt_name="pirate", handle_io=False)

    st.title("My First Streamlit App")
    st.write("Hello, welcome to my app!")
    
    if st.button("Click me!"):
        agent2_message = HumanMessage(content="Tell me a funny story.")

        while True:
            agent2_message = HumanMessage(content=agent2_message.content)
            agent1_message, control = agent1.execute(agent1_context, message=agent2_message)
            print(agent1_message.content)
            st.write("AGENT 1: " + agent1_message.content)
            sleep(2)

            agent1_message = HumanMessage(content=agent1_message.content)
            agent2_message, control = agent2.execute(agent2_context, message=agent1_message)
            print(agent2_message.content)
            st.write("AGENT 2: " + agent2_message.content)
            sleep(2)

if __name__ == "__main__":
    # main()
    semantic_memory()


