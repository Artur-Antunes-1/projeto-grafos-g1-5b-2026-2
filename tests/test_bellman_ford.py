# [IA] OpenAI Codex - geração assistida de testes de ciclos e caminhos mínimos.
from math import inf

import networkx as nx

from src.graphs.algorithms import bellman_ford, reconstruct_path
from src.graphs.graph import DirectedGraph


def test_bellman_ford_negative_weights_without_negative_cycle_match_oracle():
    graph = DirectedGraph()
    edges = [("s", "a", 4), ("s", "b", 5), ("a", "b", -2), ("b", "t", 3), ("t", "a", 0)]
    for edge in edges:
        graph.add_edge(*edge)
    graph.add_node("z")
    result = bellman_ford(graph, "s")
    oracle = nx.DiGraph()
    oracle.add_weighted_edges_from(edges)
    assert {n: d for n, d in result["distance"].items() if d != inf} == nx.single_source_bellman_ford_path_length(oracle, "s")
    assert reconstruct_path(result["parent"], "s", "t") == ["s", "a", "b", "t"]
    assert result["negative_cycle"] == []
    assert result["affected"] == set()


def test_bellman_ford_returns_valid_negative_cycle_and_all_affected_vertices():
    graph = DirectedGraph()
    for edge in [("s", "a", 1), ("a", "b", -3), ("b", "a", 1), ("b", "t", 5), ("s", "safe", 2)]:
        graph.add_edge(*edge)
    result = bellman_ford(graph, "s")
    cycle = result["negative_cycle"]
    assert len(cycle) >= 2 and cycle[0] == cycle[-1]
    weights = {(u, v): w for u, v, w in graph.edges()}
    assert sum(weights[(u, v)] for u, v in zip(cycle, cycle[1:])) < 0
    assert result["affected"] == {"a", "b", "t"}
    assert all(result["distance"][v] == -inf for v in result["affected"])
    assert result["distance"]["safe"] == 2
    assert result["distance"]["s"] == 0


def test_bellman_ford_ignores_unreachable_negative_cycle():
    graph = DirectedGraph()
    for edge in [("s", "t", 2), ("a", "b", -3), ("b", "a", 1)]:
        graph.add_edge(*edge)
    result = bellman_ford(graph, "s")
    assert result["negative_cycle"] == []
    assert result["affected"] == set()
    assert result["distance"]["a"] == inf


def test_bellman_ford_negative_self_loop_and_disjoint_reachable_cycles():
    graph = DirectedGraph()
    for edge in [("s", "a", 0), ("a", "a", -1), ("s", "b", 0), ("b", "c", -2), ("c", "b", 1)]:
        graph.add_edge(*edge)
    result = bellman_ford(graph, "s")
    assert result["affected"] == {"a", "b", "c"}
    assert result["negative_cycle"][0] == result["negative_cycle"][-1]


def test_bellman_ford_single_vertex_negative_self_loop():
    graph = DirectedGraph()
    graph.add_edge("s", "s", -1)
    result = bellman_ford(graph, "s")
    assert result["negative_cycle"] == ["s", "s"]
    assert result["distance"]["s"] == -inf
