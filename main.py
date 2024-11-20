import streamlit as st
from graphviz import Digraph
import json
import re

from collections import defaultdict

class Node:
    """Represents a node in the derivation tree."""
    def __init__(self, value, children=None):
        self.value = value
        self.children = children or []

    def __str__(self, level=0):
        result = "  " * level + str(self.value) + "\n"
        for child in self.children:
            result += child.__str__(level + 1)
        return result

def cyk_parser(grammar, string):
    """Implements the CYK algorithm and returns the parsing table."""
    n = len(string)
    table = [[set() for _ in range(n)] for _ in range(n)]

    # Reverse the grammar for easy lookup
    reversed_grammar = defaultdict(list)
    for lhs, productions in grammar.items():
        for rhs in productions:
            reversed_grammar[tuple(rhs)].append(lhs)

    # Fill the table for single characters
    for i in range(n):
        for lhs, rhs_list in grammar.items():
            for rhs in rhs_list:
                if len(rhs) == 1 and rhs[0] == string[i]:
                    table[i][i].add(lhs)

    # Fill the table for longer substrings
    for length in range(2, n + 1):  # Length of the substring
        for i in range(n - length + 1):
            j = i + length - 1
            for k in range(i, j):
                for B in table[i][k]:
                    for C in table[k + 1][j]:
                        for lhs, rhs_list in grammar.items():
                            for rhs in rhs_list:
                                if len(rhs) == 2 and rhs[0] == B and rhs[1] == C:
                                    table[i][j].add(lhs)

    return table

def build_derivation_tree(table, grammar, string):
    """Builds the derivation tree from the CYK table using memoization."""
    n = len(string)
    start_symbol = list(grammar.keys())[0]  # Assume the first key is the start symbol

    # Check if the start symbol is in the top-right cell
    if start_symbol not in table[0][n - 1]:
        return None

    # Cache to store results of (i, j, symbol)
    cache = {}

    def helper(i, j, symbol):
        # Use memoization to avoid recomputing
        if (i, j, symbol) in cache:
            return cache[(i, j, symbol)]

        # Base case: single character
        if i == j:
            for lhs, rhs_list in grammar.items():
                for rhs in rhs_list:
                    if len(rhs) == 1 and rhs[0] == string[i]:
                        node = Node(lhs, [Node(string[i])])
                        cache[(i, j, symbol)] = node
                        return node
            cache[(i, j, symbol)] = None
            return None

        # Try all possible ways to derive the symbol
        for lhs, rhs_list in grammar.items():
            for rhs in rhs_list:
                if len(rhs) == 2:
                    for k in range(i, j):
                        left, right = rhs
                        if left in table[i][k] and right in table[k + 1][j]:
                            left_subtree = helper(i, k, left)
                            right_subtree = helper(k + 1, j, right)
                            if left_subtree and right_subtree:
                                node = Node(lhs, [left_subtree, right_subtree])
                                cache[(i, j, symbol)] = node
                                return node

        # If no valid derivation found, cache and return None
        cache[(i, j, symbol)] = None
        return None

    return helper(0, n - 1, start_symbol)


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

