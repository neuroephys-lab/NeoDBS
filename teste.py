import json
import pprint
import matplotlib.pyplot as plt
import networkx as nx

def data_structure():
    file_path = 'C:\\Users\\OCD\\Desktop\\DATA\RN\\2024-11-11\\Report_Json_Session_Report_20241125T163059.json'
    file = open(file_path,'r',encoding='utf-8')
    data = json.load(file)

    def print_structure(data,depth=1,indent=0):
        if isinstance(data,dict):
            for key, value in data.items():
                print(" " * indent + f"- List of {type(data[0]).__name__}") 
                if isinstance(data[0], (dict,list)) and depth>0:
                    print_structure(data[0],depth-1, indent+4)



    #print_structure(data)
    pprint.pprint(data,depth=2)


    structure = pprint.pformat(data,depth=2)

    def add_nodes_edges(graph, structure, parent="Root"):
        """Parses a pprint-formatted structure and adds nodes/edges to the graph."""
        lines = structure.split("\n")  # Split into lines
        parent_stack = [parent]  # Stack to track parent nodes
        
        for line in lines:
            stripped_line = line.strip()
            
            # Ignore empty lines
            if not stripped_line:
                continue

            # Determine indentation level (each indentation = 4 spaces in pprint)
            indent_level = (len(line) - len(stripped_line)) // 4
            
            # Extract node label (handling dictionary keys and list indexes)
            if ":" in stripped_line:  # Dictionary entry
                key = stripped_line.split(":")[0]
            else:  # List item
                key = stripped_line
            
            node_label = key.strip("'\"")  # Clean up quotes if any
            graph.add_node(node_label)  # Add the node
            
            # Find the correct parent based on indentation
            while len(parent_stack) > indent_level + 1:
                parent_stack.pop()
            
            graph.add_edge(parent_stack[-1], node_label)  # Connect node to parent
            parent_stack.append(node_label)  # Push to stack

        return graph


    # Create a directed graph
    G = nx.DiGraph()

    add_nodes_edges(G, structure, parent="Root")

    def plot_structure(G):
        # Plot the graph
        plt.figure(figsize=(40,40))
        pos = nx.circular_layout(G) # Layout the nodes
        nx.draw(G, pos, with_labels=True, node_size=2000, node_color="lightblue", edge_color="gray", font_size=8)
        plt.title("Mind Map of JSON Structure")

        print(f"nodes: {G.nodes()}")
        print(f"nodes: {G.edges()}")

        plt.show()

def compare_dict(dict1, dict2):
    keys1 = set(dict1)
    keys2 = set(dict2)

    missing = keys1-keys2
    extra = keys2-keys1

    if missing: 
        print(f"Missing keys in 2: {missing}")
    if extra: 
        print(f"Extra keys in 2: {extra}")
    if not 'IndefiniteStreaming' in dict2.keys(): 
        print('NO INDEFINITE') 
    else: print('ok')