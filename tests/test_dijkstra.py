# [IA] OpenAI Codex - geração assistida de testes próprios com oráculo NetworkX.
from math import inf

import networkx as nx
import pytest

from src.graphs.algorithms import dijkstra, reconstruct_path
from src.graphs.graph import DirectedGraph


def test_dijkstra_weighted_shortest_paths_match_oracle():
    graph = DirectedGraph()
    edges = [("s", "a", 10), ("s", "b", 2), ("b", "a", 1), ("a", "t", 2), ("b", "t", 10)]
    for edge in edges:
        graph.add_edge(*edge)
    graph.add_node("z")
    result = dijkstra(graph, "s")
    oracle = nx.DiGraph()
    oracle.add_weighted_edges_from(edges)
    assert {n: d for n, d in result["distance"].items() if d != inf} == nx.single_source_dijkstra_path_length(oracle, "s")
    assert reconstruct_path(result["parent"], "s", "t") == ["s", "b", "a", "t"]
    assert result["distance"]["z"] == inf
    assert result["negative_cycle"] == []
    assert result["affected"] == set()


def test_dijkstra_rejects_negative_edge_even_unreachable():
    graph = DirectedGraph()
    graph.add_node("s")
    graph.add_edge("a", "b", -1)
    with pytest.raises(ValueError, match="negativ"):
        dijkstra(graph, "s")


def test_dijkstra_equal_distances_allow_noncomparable_node_types():
    graph = DirectedGraph()
    graph.add_edge("s", (1, 2), 0)
    graph.add_edge("s", 7, 0)
    assert dijkstra(graph, "s")["distance"][7] == 0
