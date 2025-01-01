
from collections import defaultdict
import pprint
import string
from thoughts.context import Context
from thoughts.interfaces.messaging import AIMessage
from thoughts.operations.core import Operation

import spacy
from spacy.cli import download
from spacy.util import is_package

import networkx as nx
from pyvis.network import Network
from rapidfuzz import fuzz
from nltk.corpus import wordnet as wn

class EntityExtractor(Operation):
    def __init__(self):
        model_name = "en_core_web_sm"
        if not is_package(model_name):
            download(model_name)
        self.nlp = spacy.load(model_name)

    def normalize_entity(self, entity_text):
        normalized_text = entity_text.strip().lower().translate(str.maketrans('', '', string.punctuation))
        normalized_text = str.removeprefix(normalized_text, "the ")
        normalized_text = str.removeprefix(normalized_text, "a ")
        normalized_text = str.removeprefix(normalized_text, "an ")

        return normalized_text
    
    def deduplicate_entities_similarity(self, entities, threshold=0.85):
        """Deduplicate entities based on a string similarity function."""
        unique_entities = set()
        processed_entities = set()
        
        for entity in entities:
            if entity in processed_entities:
                continue
            
            similar_entities = [entity]
            for other_entity in entities:
                if other_entity == entity or other_entity in processed_entities:
                    continue
                similarity_score = self.combined_similarity(entity, other_entity)
                if similarity_score >= threshold:
                    similar_entities.append(other_entity)
                    processed_entities.add(other_entity)
            
            # Choose one representative for the similar entities, here we take the first one
            representative_entity = similar_entities[0]
            unique_entities.add(representative_entity)
            processed_entities.add(entity)
        
        return unique_entities

    def levenshtein_similarity(self, str1, str2):
        """Calculate the Levenshtein similarity between two strings."""
        return fuzz.ratio(str1, str2) / 100  # Normalize to 0-1 range

    def combined_similarity(self, str1, str2, weights=(0.4, 0.3, 0.3)):
        """Combine different similarity measures into one score."""
        lev_sim = self.levenshtein_similarity(str1, str2)
        # jac_sim = jaccard_similarity(str1, str2)
        # cos_sim = cosine_similarity_tfidf(str1, str2)
        
        # combined_score = weights[0] * lev_sim + weights[1] * jac_sim + weights[2] * cos_sim
        combined_score = lev_sim

        return combined_score

    def extract_topics_and_entities(self, docs: list):
        topics_and_entities = set()
        for doc_text in docs:
            doc = self.nlp(doc_text)
            for entity in doc.ents:
                normalized_entity = self.normalize_entity(entity.text)
                topics_and_entities.add(normalized_entity)
        return topics_and_entities
    
    def execute(self, context: Context, docs: list):
        topics_and_entities = self.extract_topics_and_entities(docs)
        topics_and_entities = self.deduplicate_entities_similarity(topics_and_entities)
        graph = {"entities": topics_and_entities, "docs": docs}
        return graph
    
class RelationshipExtractor(Operation):
    def __init__(self, window_size: int = 5, overlap_size: int = 2):
        self.window_size = window_size
        self.overlap_size = overlap_size

    def construct_prompt2(self, doc_text, entities):
        # Construct a prompt for the LLM that includes the document text and entities
        entity_list = ', '.join(entities)
        prompt = (f"Given the following document text:\n\n{doc_text}\n\n"
            f"And the following entities: {entity_list}\n\n"
            f"Generate triples in the form (subject, predicate, object) that describe relationships between these entities.\n"
            f"Please return each triple on a new line, without numbering, in the exact format: (subject, predicate, object)")
        return prompt

    def construct_prompt(self, doc_text):
        # Construct a prompt for the LLM that includes the document text and entities
        prompt = (f"Instructions:\n"
                  f"1. Extract all entities and knowledge graph triples from the Context below.\n"
                  "2. List each entity in an Entities bulleted list. Resolve any pronouns or anaphoric references back to a named entity, if applicable. Format as: Entity.\n"
                #   f"3. List each triple in a Relationships list. Format each triple in the form (subject, predicate, object) that describe relationships between the entities.\n"
                  "3. List each triple in a Relationships bulleted list. Format each triple on a new line, without numbering, in the exact format: (subject, predicate, object)\n\n"
                  f"Context:\n\n{doc_text}\n\n")
        return prompt

    def construct_prompt4(self, doc_text):
        # Construct a prompt for the LLM that includes the document text and entities
        prompt = (f"Instructions:\n"
                  f"1. Extract all entities and knowledge graph triples from the Context below.\n"
                  "2. List each entity in an Entities bulleted list. Resolve any pronouns or anaphoric references back to a named entity, if applicable. Format as: Entity {Type of Entity}.\n"
                #   f"3. List each triple in a Relationships list. Format each triple in the form (subject, predicate, object) that describe relationships between the entities.\n"
                  "3. List each triple in a Relationships bulleted list. Format each triple on a new line, without numbering, in the exact format: (subject {Type of Subject}, predicate, object {Type of Object})\n\n"
                  f"Context:\n\n{doc_text}\n\n")
        return prompt
        
    def construct_prompt3(self, doc_text):
        # Construct a prompt for the LLM that includes the document text and entities
        prompt = (f"Instructions:\n"
                  f"1. Extract all entities and knowledge graph triples from the Context below.\n"
                  f"2. List each entity in an Entities bulleted list.\n"
                #   f"3. List each triple in a Relationships list. Format each triple in the form (subject, predicate, object) that describe relationships between the entities.\n"
                  f"3. List each triple in a Relationships bulleted list. Format each triple on a new line, without numbering, in the exact format: ([subject], [predicate], [object])\n\n"
                  f"Context:\n\n{doc_text}\n\n")
        return prompt
    
    def parse_llm_response(self, response: AIMessage):
        triples = []
        for line in response.content.splitlines():
            # Strip the leading number and period
            triple_str = line.split('. ', 1)[-1]
            # Remove the parentheses and split by comma
            triple = tuple(triple_str.strip('()').split(', '))
            if len(triple) == 3:
                triples.append(triple)
        return triples
 
    def normalize_entity(self, entity_text):
        normalized_text = entity_text.strip().lower().translate(str.maketrans('', '', string.punctuation))
        normalized_text = str.removeprefix(normalized_text, "the ")
        normalized_text = str.removeprefix(normalized_text, "a ")
        normalized_text = str.removeprefix(normalized_text, "an ")
        return normalized_text

    def extract_entities_and_relationships(self, response: AIMessage):
        """
        Extracts entities and relationships from the LLM output.

        Parameters:
        llm_output (str): The text output from the LLM.

        Returns:
        tuple: A tuple containing two lists:
            - entities: A list of entity names (strings).
            - relationships: A list of tuples representing relationships (subject, predicate, object).
        """
        entities = []
        relationships = []

        # Split the output into lines
        llm_output = response.content
        lines = llm_output.strip().split('\n')

        # Flags to track if we are currently parsing entities or relationships
        parsing_entities = False
        parsing_relationships = False

        # Iterate through each line to extract entities and relationships
        for line in lines:
            line = line.strip()  # Remove leading/trailing whitespace

            if line.startswith("Entities:"):
                parsing_entities = True
                parsing_relationships = False
                continue  # Skip the "Entities:" line itself

            if line.startswith("Relationships:"):
                parsing_entities = False
                parsing_relationships = True
                continue  # Skip the "Relationships:" line itself

            if parsing_entities and line.startswith("- "):
                entity_text = line[2:].strip()
                entity_text = self.normalize_entity(entity_text)
                entities.append(entity_text)

            # if parsing_entities and line.startswith("- "):
            #     # Extract entity name and type
            #     entity_text = line[2:].strip()
            #     if "{" in entity_text and "}" in entity_text:
            #         entity_name, entity_type = entity_text.split(" {", 1)
            #         entity_type = entity_type.rstrip("}")
            #         entity_name = self.normalize_entity(entity_name)
            #         # entities.append((entity_name, entity_type))
            #         entities.append(entity_name + " {" + entity_type + "}")
            #     else:
            #         # In case of malformed or missing type, handle gracefully
            #         entity_name = self.normalize_entity(entity_text)
            #         # entities.append((entity_name, "Unknown"))
            #         entities.append(entity_name + " {{Unknown}}")

            if parsing_relationships and line.startswith("- "):
                # Expecting a line formatted as (subject, predicate, object)
                relationship = tuple(line[2:].strip("()").split(", "))
                if len(relationship) == 3:
                    subject, predicate, obj = relationship
                    subject = self.normalize_entity(subject)
                    obj = self.normalize_entity(obj)
                    relationships.append((subject, predicate, obj))

        return entities, relationships

    def execute(self, context: Context, graph: dict):
        docs = graph.get("docs", [])

        unique_entities = set()
        unique_triples = set()

        i = 0
        while i < len(docs):
            # Calculate the end of the current window
            end = min(i + self.window_size, len(docs))

            # Create a block of text from the sliding window
            window_text = " ".join(docs[i:end]).strip()
            
            if len(window_text) == 0:
                i += self.window_size - self.overlap_size
                continue

            # Generate prompt and get LLM response
            prompt = self.construct_prompt(window_text)
            response = context.llm.respond_to_text(prompt)

            # Extract entities and relationships
            parsed_entities, parsed_triples = self.extract_entities_and_relationships(response)

            print("Extracted Entities:")
            pprint.pprint(parsed_entities)
            print("")
            print("Extracted Relationships:")
            pprint.pprint(parsed_triples)
            print("")
            
            # Add to the sets for deduplication
            unique_entities.update(parsed_entities)
            unique_triples.update(parsed_triples)

            # Move to the next window, overlapping by M documents
            i += self.window_size - self.overlap_size

        # Convert sets back to lists for final graph output
        graph["entities"] = list(unique_entities)
        graph["triples"] = list(unique_triples)

        return graph

    def execute3(self, context: Context, graph: dict):
        docs = graph["docs"]

        triples = []
        entities = []
        for doc_text in docs:
            if len(doc_text) == 0:
                continue
            prompt = self.construct_prompt(doc_text)   
            response = context.llm.respond_to_text(prompt)
            # parsed_triples = self.parse_llm_response(response)
            parsed_entities, parsed_triples = self.extract_entities_and_relationships(response)
            entities.extend(parsed_entities)
            triples.extend(parsed_triples)
        
        graph["entities"] = entities
        graph["triples"] = triples
        return graph
    
    def execute2(self, context: Context, graph: dict):
        docs = graph["docs"]
        entities = graph["entities"]

        triples = []
        for doc_text in docs:
            if len(doc_text) == 0:
                continue
            prompt = self.construct_prompt(doc_text, entities)   
            response = context.llm.respond_to_text(prompt)
            # parsed_triples = self.parse_llm_response(response)
            entities, parsed_triples = self.extract_entities_and_relationships(response)
            triples.extend(parsed_triples)
        
        graph["triples"] = triples
        return graph
    
class GraphBuilder(Operation):
    def __init__(self):
        pass
    def execute(self, context, graph):
        triples = graph["triples"]
        G = nx.DiGraph()  # Directed graph to capture the directionality of the triples
        for subject, predicate, obj in triples:
            G.add_node(subject)
            G.add_node(obj)
            G.add_edge(subject, obj, label=predicate)
        return G
    
class GraphVisualizer(Operation):
    def __init__(self):
        pass
    def execute(self, context, network_x_graph):
        net = Network(notebook=True, directed=True)
        net.from_nx(network_x_graph)

        # Customize the appearance of nodes and edges if desired
        for node in net.nodes:
            node['title'] = node['id']  # Show the node's ID on hover
            node['label'] = node['id']  # Label the node with its ID

        for edge in net.edges:
            edge['title'] = edge['label']  # Show the edge label on hover
            edge['label'] = edge['label']  # Label the edge with its predicate

        # Generate and save the visualization to an HTML file
        net.show("test.html")

class GraphExtractor(Operation):
    def __init__(self):
        pass
    def execute(self, context, docs: list):
        pass

class EntitySummarizer(Operation):
    def __init__(self, top_n = 5):
        self.top_n = top_n

    def execute(self, context: Context, graph):
        """
        Generates LLM summaries for each entity in the graph.

        Parameters:
        context (Context): The context containing the LLM interface.
        graph (dict): The graph containing entities and triples.

        Returns:
        dict: A dictionary where keys are entity names and values are their LLM-generated summaries.
        """
        # entities = graph.get("entities", [])
        triples = graph.get("triples", [])
        
        # Step 1: Count the number of connections for each entity
        connection_counts = defaultdict(int)
        for triple in triples:
            connection_counts[triple[0]] += 1  # Count subject
            connection_counts[triple[2]] += 1  # Count object

        # Step 2: Identify the top N entities with the most connections
        top_entities = sorted(connection_counts, key=connection_counts.get, reverse=True)[:self.top_n]

        entity_summaries = {}

        for entity in top_entities:
            # Find all triples where the entity appears
            relevant_triples = [triple for triple in triples if entity in (triple[0], triple[2])]

            if not relevant_triples:
                continue  # Skip entities with no relevant triples

            # Format triples into a text prompt for the LLM
            triples_text = "\n".join([f"{triple[0]} {triple[1]} {triple[2]}" for triple in relevant_triples])
            prompt = f"Please summarize the following information about the entity '{entity}':\n\n{triples_text}\n\nSummary:"

            # Generate the summary using the LLM
            response = context.llm.respond_to_text(prompt)
            summary = response.content.strip()  # Clean up the response

            # Store the summary in the dictionary
            entity_summaries[entity] = summary

        graph["entity-summaries"] = entity_summaries
        return graph
    
class EntityResolver(Operation):
    def __init__(self):
        pass

    def is_match(self, entity_a: str, entity_b: str):
        jac_sim = self.jaccard_similarity(entity_a, entity_b)
        # syn_match = self.synonym_match(entity_a, entity_b)
        syn_match = False

        # Combine the results: You can adjust weights or thresholds as needed
        if jac_sim > 0.5 or syn_match:
            return True

    def jaccard_similarity(self, str1, str2):
        set1 = set(str1.split())
        set2 = set(str2.split())
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union

    # def get_synonyms(self, word):
    #     synonyms = set()
    #     for synset in wn.synsets(word):
    #         for lemma in synset.lemmas():
    #             synonyms.add(lemma.name())
    #     return synonyms

    # def synonym_match(self, entity_a_name, entity_b_name):
    #     words_a = entity_a_name.split()
    #     words_b = entity_b_name.split()
        
    #     for word_a in words_a:
    #         synonyms_a = self.get_synonyms(word_a)
    #         if any(word_b in synonyms_a for word_b in words_b):
    #             return True
    #     return False

    def execute(self, context: Context, graph):
        """
        Resolves duplicate entities in the graph by merging them and updating triples.

        Parameters:
        graph (dict): The graph containing entities and triples.
        match_function (function): A function that takes two entity names as input and returns True if they match, otherwise False.

        Returns:
        dict: The updated graph with duplicates resolved.
        """
        entities = graph.get("entities", [])
        triples = graph.get("triples", [])

        # Step 1: Identify duplicates
        resolved_entities = {}  # Maps old entity name to resolved entity name
        processed_entities = set()

        for entity_a in entities:
            if entity_a in processed_entities:
                continue

            for entity_b in entities:
                if entity_a != entity_b and self.is_match(entity_a, entity_b):
                    # Decide which entity to keep (could be based on some criteria; here we'll keep entity_a)
                    resolved_entities[entity_b] = entity_a
                    processed_entities.add(entity_b)

            processed_entities.add(entity_a)

        # Step 2: Update triples to point to resolved entities
        updated_triples = []
        for triple in triples:
            subject, predicate, obj = triple
            resolved_subject = resolved_entities.get(subject, subject)
            resolved_object = resolved_entities.get(obj, obj)
            updated_triples.append((resolved_subject, predicate, resolved_object))

        # Step 3: Remove duplicates from entities
        updated_entities = [entity for entity in entities if entity not in resolved_entities or resolved_entities[entity] == entity]

        # Update the graph
        graph["entities"] = updated_entities
        graph["triples"] = updated_triples

        return graph
