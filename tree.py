from graphviz import Digraph

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
    start_symbol = "S"

    if start_symbol not in table[0][n - 1]:
        return None

    def helper(i, j, symbol):
        if i == j:
            return Node(symbol, [Node(string[i])])
        for k in range(i, j):
            for lhs, rhs_list in grammar.items():
                for rhs in rhs_list:
                    if len(rhs) == 2 and rhs[0] in table[i][k] and rhs[1] in table[k + 1][j]:
                        left = helper(i, k, rhs[0])
                        right = helper(k + 1, j, rhs[1])
                        return Node(lhs, [left, right])
        return None

    return helper(0, n - 1, start_symbol)
