import streamlit as st
from graphviz import Digraph
import json
import re

class Node:
    def __init__(self, symbol, children=None):
        self.symbol = symbol
        self.children = children or []

    def to_graphviz(self, graph=None, parent_id=None, node_id=0):
        """
        Converts the tree to a Graphviz Digraph object with more robust handling.
        """
        if graph is None:
            graph = Digraph(format='svg', engine='dot')
            graph.attr('node', shape='rectangle')
        
        current_id = str(node_id)
        # Escape special characters in node labels
        safe_symbol = self.symbol.replace('"', '\\"')
        graph.node(current_id, label=safe_symbol)

        if parent_id is not None:
            graph.edge(parent_id, current_id)
        
        next_id = node_id + 1
        for child in self.children:
            next_id = child.to_graphviz(graph, current_id, next_id)
        
        return next_id

def validate_grammar_input(grammar_input):
    """
    Validate grammar input and provide detailed error messages.
    """
    # Check for basic structural integrity
    if not grammar_input or len(grammar_input.strip()) == 0:
        raise ValueError("Grammar cannot be empty.")
    
    # Check for valid rules
    lines = grammar_input.strip().split('\n')
    for line in lines:
        if not re.match(r'^\s*[A-Z]\s*->\s*[a-zA-Z\s|]+$', line):
            raise ValueError(f"Invalid grammar rule format: {line}")
    
    return True

def build_derivation_tree(table, grammar, string):
    """Builds the derivation tree from the CYK table with an iterative approach to avoid deep recursion."""
    n = len(string)
    start_symbol = list(grammar.keys())[0]  # First key is typically the start symbol

    # Check if the start symbol is in the top-right cell
    if start_symbol not in table[0][n - 1]:
        return None

    # Iterative approach using a stack
    stack = [(0, n - 1, start_symbol, None)]  # (i, j, symbol, parent_node)
    root = None
    nodes = {}  # Map (i, j, symbol) -> Node

    while stack:
        i, j, symbol, parent_node = stack.pop()

        # If the node already exists, link it
        if (i, j, symbol) in nodes:
            node = nodes[(i, j, symbol)]
        else:
            # Create a new node
            node = Node(symbol)
            nodes[(i, j, symbol)] = node

        # Link the node to its parent if applicable
        if parent_node:
            parent_node.children.append(node)

        # Assign root if it hasn't been set
        if root is None:
            root = node

        # Base case: Single character derivation
        if i == j:
            node.children.append(Node(string[i]))
            continue

        # Recursive case: Add children based on grammar
        for lhs, rhs_list in grammar.items():
            for rhs in rhs_list:
                if len(rhs) == 2:  # Binary rule
                    left, right = rhs
                    for k in range(i, j):
                        if left in table[i][k] and right in table[k + 1][j]:
                            stack.append((i, k, left, node))
                            stack.append((k + 1, j, right, node))
                            break
                elif len(rhs) == 1:  # Unary rule
                    if rhs[0] in table[i][j]:
                        stack.append((i, j, rhs[0], node))
                        break

    return root


def cyk_parser(grammar, input_string):
    """
    Enhanced CYK parser with more robust error checking and rule handling.
    """
    # Validate input
    if not input_string:
        raise ValueError("Input string cannot be empty.")
    
    n = len(input_string)
    table = [[set() for _ in range(n)] for _ in range(n)]

    # Base case: Fill the diagonal (single character matches)
    for i in range(n):
        char = input_string[i]
        for lhs, rhs_list in grammar.items():
            for production in rhs_list:
                if len(production) == 1 and production[0] == char:
                    table[i][i].add(lhs)
    
    # Recursive case: Fill the table for substrings of length 2 to n
    for length in range(2, n + 1):
        for start in range(n - length + 1):
            end = start + length - 1
            for split in range(start, end):
                for lhs, rhs_list in grammar.items():
                    for production in rhs_list:
                        # Support both binary and unary rules
                        if len(production) == 2:
                            left, right = production
                            if left in table[start][split] and right in table[split + 1][end]:
                                table[start][end].add(lhs)
                        elif len(production) == 1:
                            # Unary rule propagation
                            if production[0] in table[start][end]:
                                table[start][end].add(lhs)
    
    # Check if any symbol is in the top-right cell
    return len(table[0][n - 1]) > 0, table

def text_to_json(cfg_text):
    """
    Converts a text-based CFG into JSON format with improved parsing.
    """
    grammar = {}
    lines = cfg_text.strip().split('\n')
    for line in lines:
        # Use regex to split on -> and handle potential whitespace
        parts = re.split(r'\s*->\s*', line.strip())
        if len(parts) != 2:
            raise ValueError(f"Invalid grammar rule format: {line}")
        
        lhs = parts[0].strip()
        rhs_rules = [r.strip().split() for r in parts[1].split('|')]
        
        if lhs in grammar:
            grammar[lhs].extend(rhs_rules)
        else:
            grammar[lhs] = rhs_rules
    
    return grammar

# Streamlit UI Configuration
st.set_page_config(
    page_title="CFG Parser",
    page_icon="🔍",
    layout="wide"
)

# Main App
st.title("Context-Free Grammar (CFG) Parser")
st.markdown(""" 
    ### Parse and Visualize Context-Free Grammars
    - Enter a grammar in JSON or Text format
    - Specify an input string to parse
    - Visualize the derivation tree
""")

# Sidebar Configuration
st.sidebar.header("Grammar Input")
input_mode = st.sidebar.radio("Input Mode", ["Text", "JSON"])

# Error handling wrapper for grammar input
try:
    if input_mode == "Text":
        grammar_text_input = st.sidebar.text_area(
            "Enter Grammar (Text Format)", 
            value="S -> A B | B A | A\nA -> a | S\nB -> b",
            height=200
        )
        validate_grammar_input(grammar_text_input)
        grammar = text_to_json(grammar_text_input)
        
    else:  # JSON Mode
        grammar_input = st.sidebar.text_area(
            "Enter Grammar (JSON Format)", 
            value='{"S": [["A", "B"], ["B", "A"], ["A"]], "A": [["a"], ["S"]], "B": [["b"]]}',
            height=200
        )
        grammar = json.loads(grammar_input)

    string_input = st.sidebar.text_input("Enter the string to parse", value="ab")
    
    # Parse Button
    if st.sidebar.button("Parse Grammar", type="primary"):
        # Validate input string
        if not string_input:
            st.error("Please enter a valid input string.")
        else:
            try:
                is_valid, table = cyk_parser(grammar, string_input)
                
                if is_valid:
                    st.success(f"✅ The string '{string_input}' is valid in the given grammar!")
                    
                    # Generate and display derivation tree
                    tree = build_derivation_tree(table, grammar, string_input)
                    if tree:
                        st.subheader("Derivation Tree Visualization")
                        graph = Digraph(format="svg")
                        tree.to_graphviz(graph)
                        st.graphviz_chart(graph.source)
                    else:
                        st.warning("Could not generate a complete derivation tree.")
                else:
                    st.error(f"❌ The string '{string_input}' is not valid in the given grammar.")
            
            except Exception as e:
                st.error(f"Parsing error: {str(e)}")

except (ValueError, json.JSONDecodeError) as e:
    st.sidebar.error(f"Grammar Input Error: {str(e)}")
except Exception as e:
    st.sidebar.error(f"Unexpected error: {str(e)}")

# Contributor Box at the bottom-right
st.markdown("""
    <div style="position: fixed; bottom: 10px; right: 10px; padding: 10px; border: 2px solid #4CAF50; border-radius: 5px; background-color: #333333; color: white;">
        <h4 style="margin: 0; font-weight: bold;">Team Members:</h4>
        <p style="margin: 5px 0;">Uday Kumar Gupta (2023UAI1800)</p>
        <p style="margin: 0;">Gaurav Sharma (2023UAI1810)</p>
        <p></p>
    </div>
""", unsafe_allow_html=True)

