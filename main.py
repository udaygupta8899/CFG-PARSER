import streamlit as st
from graphviz import Digraph
import json
import re

class Node:
    """Represents a node in the derivation tree."""
    def __init__(self, value, children=None):
        self.value = value
        self.children = children or []

    def to_graphviz(self, graph=None, parent_id=None, node_id=0):
        """
        Converts the tree to a Graphviz Digraph object.
        """
        if graph is None:
            graph = Digraph(format='svg', engine='dot')
            graph.attr('node', shape='rectangle')
        
        current_id = str(node_id)
        safe_label = self.value.replace('"', '\\"')
        graph.node(current_id, label=safe_label)

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
    if not grammar_input.strip():
        raise ValueError("Grammar cannot be empty.")
    
    lines = grammar_input.strip().split('\n')
    for line in lines:
        if not re.match(r'^\s*[A-Z]\s*->\s*[a-zA-Z\s|]+$', line):
            raise ValueError(f"Invalid grammar rule format: {line}")
    return True

def text_to_json(cfg_text):
    """
    Converts a text-based CFG into JSON format.
    """
    grammar = {}
    lines = cfg_text.strip().split('\n')
    for line in lines:
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

def cyk_parser(grammar, input_string):
    """
    Implements the CYK algorithm and builds a parse table.
    """
    n = len(input_string)
    table = [[set() for _ in range(n)] for _ in range(n)]
    backtrack = [[{} for _ in range(n)] for _ in range(n)]

    # Base case: Fill the diagonal for single characters
    for i, char in enumerate(input_string):
        for lhs, rhs_list in grammar.items():
            for rhs in rhs_list:
                if len(rhs) == 1 and rhs[0] == char:
                    table[i][i].add(lhs)
                    backtrack[i][i][lhs] = [Node(char)]

    # Recursive case: Fill for substrings of length 2 to n
    for length in range(2, n + 1):
        for start in range(n - length + 1):
            end = start + length - 1
            for split in range(start, end):
                for lhs, rhs_list in grammar.items():
                    for rhs in rhs_list:
                        if len(rhs) == 2:
                            left, right = rhs
                            if left in table[start][split] and right in table[split + 1][end]:
                                table[start][end].add(lhs)
                                backtrack[start][end][lhs] = [Node(lhs, [
                                    backtrack[start][split][left][0],
                                    backtrack[split + 1][end][right][0]
                                ])]

    return table, backtrack

def build_derivation_tree(table, backtrack, grammar, string):
    """
    Constructs a derivation tree from the CYK table.
    """
    n = len(string)
    start_symbol = list(grammar.keys())[0]

    if start_symbol in table[0][n - 1]:
        return backtrack[0][n - 1][start_symbol][0]
    return None

# Streamlit UI Configuration
st.set_page_config(
    page_title="CFG Parser",
    page_icon="📘",
    layout="wide"
)

st.title("Context-Free Grammar (CFG) Parser")
st.markdown("""
### Parse and Visualize Context-Free Grammars
- Enter a grammar in **Text** or **JSON** format.
- Specify an input string to parse.
- Visualize the derivation tree.
""")

# Sidebar Configuration
st.sidebar.header("Grammar Input")
input_mode = st.sidebar.radio("Input Mode", ["Text", "JSON"])

try:
    if input_mode == "Text":
        grammar_text_input = st.sidebar.text_area(
            "Enter Grammar (Text Format)", 
            value="S -> A B | B A | A C\nA -> a | S\nB -> b\nC -> c",
            height=200
        )
        validate_grammar_input(grammar_text_input)
        grammar = text_to_json(grammar_text_input)
    else:  # JSON Mode
        grammar_input = st.sidebar.text_area(
            "Enter Grammar (JSON Format)", 
            value='{"S": [["A", "B"], ["B", "A"], ["A", "C"]], "A": [["a"], ["S"]], "B": [["b"]], "C": [["c"]]}',
            height=200
        )
        grammar = json.loads(grammar_input)

    string_input = st.sidebar.text_input("Enter the string to parse", value="ac")
    
    if st.sidebar.button("Parse Grammar"):
        if not string_input:
            st.error("Input string cannot be empty.")
        else:
            try:
                table, backtrack = cyk_parser(grammar, string_input)
                tree = build_derivation_tree(table, backtrack, grammar, string_input)

                if tree:
                    st.success(f"✅ The string '{string_input}' is valid in the given grammar!")
                    graph = Digraph(format="svg")
                    tree.to_graphviz(graph)
                    st.graphviz_chart(graph.source)
                else:
                    st.error(f"❌ The string '{string_input}' is not valid in the given grammar.")
            except Exception as e:
                st.error(f"Parsing error: {str(e)}")

except ValueError as e:
    st.sidebar.error(f"Grammar Input Error: {str(e)}")
except Exception as e:
    st.sidebar.error(f"Unexpected Error: {str(e)}")


# Contributor Box at the bottom-right
st.markdown("""
    <div style="position: fixed; bottom: 10px; right: 10px; padding: 10px; border: 2px solid #4CAF50; border-radius: 5px; background-color: #333333; color: white;">
        <h4 style="margin: 0; font-weight: bold;">Team Members:</h4>
        <p style="margin: 5px 0;">Uday Kumar Gupta (2023UAI1800)</p>
        <p style="margin: 0;">Gaurav Sharma (2023UAI1810)</p>
        <p></p>
    </div>
""", unsafe_allow_html=True)

