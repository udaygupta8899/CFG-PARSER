import numpy as np

def cyk_parser(grammar, string):
    """
    Implements the CYK algorithm for parsing.
    grammar: dict - CFG in CNF (e.g., {"S": [["A", "B"], ["B", "A"]], ...})
    string: str - Input string to parse.
    Returns: bool, derivation_tree
    """
    n = len(string)
    r = len(grammar)
    table = [[set() for _ in range(n)] for _ in range(n)]
    rules = {tuple(rhs): lhs for lhs, rhs_list in grammar.items() for rhs in rhs_list}

    # Fill the diagonal
    for i, symbol in enumerate(string):
        for lhs, rhs_list in grammar.items():
            if [symbol] in rhs_list:
                table[i][i].add(lhs)

    # Fill upper triangle
    for length in range(2, n + 1):  # Length of the span
        for i in range(n - length + 1):
            j = i + length - 1
            for k in range(i, j):
                for A in table[i][k]:
                    for B in table[k + 1][j]:
                        if (A, B) in rules:
                            table[i][j].add(rules[(A, B)])

    # Check if start symbol is in the top-right cell
    start_symbol = "S"
    return start_symbol in table[0][n - 1], table
