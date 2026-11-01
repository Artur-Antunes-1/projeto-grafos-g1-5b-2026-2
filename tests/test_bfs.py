# [IA] OpenAI Codex - geração assistida de testes de BFS e reconstrução.
from math import inf

import pytest

from src.graphs.algorithms import bfs, reconstruct_path
from src.graphs.graph import DirectedGraph


def test_bfs_levels_order_and_unreachable():
    graph = DirectedGraph()
    for u, v, w in [("s", "a", 100), ("s", "b", 1), ("a", "c", -5), ("b", "c", 1)]:
        graph.add_edge(u, v, w)
    graph.add_node("z")
    result = bfs(graph, "s")
    assert result["order"] == ["s", "a", "b", "c"]
    assert result["distance"] == {"s": 0, "a": 1, "b": 1, "c": 2, "z": inf}
    assert reconstruct_path(result["parent"], "s", "c") == ["s", "a", "c"]
    assert reconstruct_path(result["parent"], "s", "z") == []
    assert reconstruct_path(result["parent"], "s", "s") == ["s"]


def test_reconstruct_rejects_broken_or_cyclic_parent_chain():
    assert reconstruct_path({"s": None, "a": "b", "b": "a"}, "s", "a") == []
    assert reconstruct_path({"s": None}, "s", "missing") == []


def test_bfs_missing_source_is_explicit():
    with pytest.raises(ValueError, match="[Oo]rigem"):
        bfs(DirectedGraph(), "ausente")


def test_bfs_deep_graph_is_iterative():
    graph = DirectedGraph()
    for i in range(1500):
        graph.add_edge(i, i + 1, 1)
    assert bfs(graph, 0)["distance"][1500] == 1500


@pytest.mark.parametrize("algorithm", ["bfs", "dfs", "dijkstra", "bellman_ford"])
def test_parent_paths_allow_none_as_hashable_node_without_faking_unreachable(algorithm):
    from src.graphs import algorithms

    graph = DirectedGraph()
    graph.add_edge("s", None, 2)
    graph.add_edge(None, "t", 3)
    graph.add_node("z")
    result = getattr(algorithms, algorithm)(graph, "s")
    assert reconstruct_path(result["parent"], "s", "t") == ["s", None, "t"]
    assert reconstruct_path(result["parent"], "s", "z") == []
