import streamlit as st
from parser import cyk_parser
from tree import build_derivation_tree
from graphviz import Digraph
import json
import re

# Title and Description
st.title("CFG Parser with Derivation Tree Visualization")
st.write("Enter a Context-Free Grammar (CFG) and a string to check if the string belongs to the language defined by the grammar.")

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


# Sidebar Inputs
st.sidebar.header("Input CFG and String")
input_mode = st.sidebar.radio("Input Mode", ["JSON", "Text"])

if input_mode == "JSON":
    grammar_input = st.sidebar.text_area(
        "Enter Grammar (JSON Format)", 
        value='{"S": [["A", "B"], ["B", "A"]], "A": [["a"]], "B": [["b"]]}'
    )
    try:
        grammar = json.loads(grammar_input)
    except json.JSONDecodeError:
        st.error("Invalid JSON grammar format. Please provide a valid JSON input.")
        st.stop()

elif input_mode == "Text":
    grammar_text_input = st.sidebar.text_area(
        "Enter Grammar (Text Format)", 
        value="S -> A B | B A\nA -> a\nB -> b"
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
