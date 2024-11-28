import streamlit as st
from graphviz import Digraph
import json
import re
import sys

sys.setrecursionlimit(3000)

# Node class to represent the derivation tree
class Node:
    def __init__(self, value, children=None):
        self.value = value
        self.children = children or []

    def to_graphviz(self, graph=None, parent_id=None, node_id=0):
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


# Helper functions for grammar parsing and validation
def validate_grammar_input(grammar_input):
    if not grammar_input.strip():
        raise ValueError("Grammar cannot be empty.")
    for line in grammar_input.strip().split('\n'):
        if not re.match(r'^\s*[A-Z]\s*->\s*[a-zA-Z\s|]+$', line):
            raise ValueError(f"Invalid grammar rule format: {line}")
    return True


def text_to_json(cfg_text):
    grammar = {}
    for line in cfg_text.strip().split('\n'):
        parts = re.split(r'\s*->\s*', line.strip())
        if len(parts) != 2:
            raise ValueError(f"Invalid grammar rule format: {line}")
        lhs = parts[0].strip()
        rhs_rules = [r.strip().split() for r in parts[1].split('|')]
        grammar[lhs] = grammar.get(lhs, []) + rhs_rules
    return grammar


def cyk_parser(grammar, input_string):
    n = len(input_string)
    table = [[set() for _ in range(n)] for _ in range(n)]
    backtrack = [[{} for _ in range(n)] for _ in range(n)]

    for i, char in enumerate(input_string):
        for lhs, rhs_list in grammar.items():
            for rhs in rhs_list:
                if len(rhs) == 1 and rhs[0] == char:
                    table[i][i].add(lhs)
                    backtrack[i][i][lhs] = [(i, i, char)]

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
                                backtrack[start][end].setdefault(lhs, []).append((split, left, right))
    return table, backtrack


def build_derivation_tree(table, grammar, string):
    n = len(string)
    start_symbol = list(grammar.keys())[0]

    def construct_tree(start, end, symbol):
        if start == end:
            for rhs in grammar[symbol]:
                if len(rhs) == 1 and rhs[0] == string[start]:
                    return Node(symbol, [Node(string[start])])
            return None

        node = Node(symbol)
        if symbol in backtrack[start][end]:
            for split, left, right in backtrack[start][end][symbol]:
                left_node = construct_tree(start, split, left)
                right_node = construct_tree(split + 1, end, right)
                if left_node and right_node:
                    node.children = [left_node, right_node]
                    break
        return node

    return construct_tree(0, n - 1, start_symbol) if start_symbol in table[0][n - 1] else None


# Streamlit App
st.set_page_config(page_title="CYK Parser", page_icon="📘", layout="wide")

st.title("CYK Parser for Context-Free Grammars")
st.markdown("""
### Features:
- Parse a **CFG** and visualize its derivation tree.
- Input grammar in **Text** or **JSON** format.
""")

# Sidebar
st.sidebar.header("Grammar Input")
input_mode = st.sidebar.radio("Input Mode", ["Text", "JSON"])

try:
    if input_mode == "Text":
        grammar_text_input = st.sidebar.text_area(
            "Enter Grammar (Text Format)",
            value="S -> A X | B A | A C\nX -> B C\nA -> a | S\nB -> b\nC -> c",
            height=200,
        )
        validate_grammar_input(grammar_text_input)
        grammar = text_to_json(grammar_text_input)
    else:
        grammar_input = st.sidebar.text_area(
            "Enter Grammar (JSON Format)",
            value='{"S": [["A", "X"], ["B", "A"], ["A", "C"]],"X":[["B","C"]], "A": [["a"], ["S"]], "B": [["b"]], "C": [["c"]]}',
            height=200,
        )
        grammar = json.loads(grammar_input)

    string_input = st.sidebar.text_input("Enter String to Parse", value="abc")

    if st.sidebar.button("Parse"):
        if not string_input:
            st.error("Input string cannot be empty.")
        else:
            table, backtrack = cyk_parser(grammar, string_input)
            tree = build_derivation_tree(table, grammar, string_input)

            if tree:
                st.success(f"The string '{string_input}' is valid!")
                graph = Digraph(format="svg")
                tree.to_graphviz(graph)
                st.graphviz_chart(graph.source)
            else:
                st.error(f"The string '{string_input}' is invalid in the given grammar.")
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
