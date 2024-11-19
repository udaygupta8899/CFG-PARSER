import streamlit as st
from graphviz import Digraph
import json

class Node:
    def __init__(self, symbol, children=None):
        self.symbol = symbol
        self.children = children or []

    def to_graphviz(self, graph=None, parent_id=None, node_id=0):
        """
        Converts the tree to a Graphviz Digraph object.
        """
        if graph is None:
            graph = Digraph(format='png')
        
        current_id = str(node_id)
        graph.node(current_id, self.symbol)

        if parent_id is not None:
            graph.edge(parent_id, current_id)
        
        next_id = node_id + 1
        for child in self.children:
            next_id = child.to_graphviz(graph, current_id, next_id)
        
        return next_id

def build_derivation_tree(table, grammar, string):
    """Builds the derivation tree from the CYK table."""
    n = len(string)
    start_symbol = list(grammar.keys())[0]  # First key is typically the start symbol

    # Check if the start symbol is in the top-right cell
    if start_symbol not in table[0][n - 1]:
        return None

    def helper(i, j, symbol):
        # Base case: single character 
        if i == j:
            for lhs, rhs_list in grammar.items():
                for rhs in rhs_list:
                    if len(rhs) == 1 and rhs[0] == string[i]:
                        return Node(lhs, [Node(string[i])])
            return None

        # Try all possible ways to derive the symbol
        for k in range(i, j):
            for lhs, rhs_list in grammar.items():
                for rhs in rhs_list:
                    # Support both binary and unary rules
                    if len(rhs) == 2 and rhs[0] in table[i][k] and rhs[1] in table[k + 1][j]:
                        left = helper(i, k, rhs[0])
                        right = helper(k + 1, j, rhs[1])
                        if left and right:
                            return Node(lhs, [left, right])
                    elif len(rhs) == 1 and rhs[0] in table[i][j]:
                        # Unary rule support
                        inner = helper(i, j, rhs[0])
                        if inner:
                            return Node(lhs, [inner])
        return None

    return helper(0, n - 1, start_symbol)

def cyk_parser(grammar, input_string):
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
    start_symbol = list(grammar.keys())[0]
    return len(table[0][n - 1]) > 0, table

def text_to_json(cfg_text):
    """
    Converts a text-based CFG into JSON format.
    cfg_text: str - Input CFG in text form.
    Returns: dict - CFG in JSON format.
    """
    grammar = {}
    lines = cfg_text.strip().split('\n')
    for line in lines:
        lhs, rhs = line.split('->')
        lhs = lhs.strip()
        rhs_rules = [r.strip().split() for r in rhs.split('|')]
        if lhs in grammar:
            grammar[lhs].extend(rhs_rules)
        else:
            grammar[lhs] = rhs_rules
    return grammar

# Streamlit UI
st.title("CFG Parser with Derivation Tree Visualization")
st.write("Enter a Context-Free Grammar (CFG) and a string to check if the string belongs to the language.")

# Sidebar Inputs
st.sidebar.header("Input CFG and String")
input_mode = st.sidebar.radio("Input Mode", ["JSON", "Text"])

if input_mode == "JSON":
    grammar_input = st.sidebar.text_area(
        "Enter Grammar (JSON Format)", 
        value='{"S": [["A", "B"], ["B", "A"], ["A"]], "A": [["a"], ["S"]], "B": [["b"]]}'
    )
    try:
        grammar = json.loads(grammar_input)
    except json.JSONDecodeError:
        st.error("Invalid JSON grammar format. Please provide a valid JSON input.")
        st.stop()

elif input_mode == "Text":
    grammar_text_input = st.sidebar.text_area(
        "Enter Grammar (Text Format)", 
        value="S -> A B | B A | A\nA -> a | S\nB -> b"
    )
    try:
        grammar = text_to_json(grammar_text_input)
        st.sidebar.success("Grammar successfully converted to JSON:")
        st.sidebar.json(grammar)
    except ValueError as e:
        st.sidebar.error(f"Invalid grammar format: {e}")
        st.stop()

string_input = st.sidebar.text_input("Enter the string to parse", value="ab")

# Parse Button
if st.sidebar.button("Parse"):
    is_valid, table = cyk_parser(grammar, string_input)
    if is_valid:
        st.success("The string is valid and belongs to the language!")
        
        tree = build_derivation_tree(table, grammar, string_input)
        if tree:
            st.subheader("Derivation Tree")
            graph = Digraph(format="svg")
            tree.to_graphviz(graph)
            st.graphviz_chart(graph.source)
        else:
            st.error("Failed to generate derivation tree.")
    else:
        st.error("The string is invalid and does not belong to the language.")
