# [IA] OpenAI Codex - geração assistida de testes de DFS iterativa.
from src.graphs.algorithms import dfs
from src.graphs.graph import DirectedGraph


def test_dfs_four_edge_types_timestamps_and_cycle():
    graph = DirectedGraph()
    for u, v in [("s", "a"), ("s", "b"), ("s", "c"), ("a", "b"), ("b", "a"), ("c", "b")]:
        graph.add_edge(u, v, 1)
    graph.add_node("isolado")
    result = dfs(graph, "s")
    assert result["order"] == ["s", "a", "b", "c"]
    assert result["classification"] == [
        ("s", "a", "arvore"), ("a", "b", "arvore"), ("b", "a", "retorno"),
        ("s", "b", "avanco"), ("s", "c", "arvore"), ("c", "b", "cruzamento"),
    ]
    assert result["has_cycle"] is True
    for u in result["order"]:
        assert result["discover"][u] < result["finish"][u]
    assert result["discover"]["s"] < result["discover"]["a"] < result["finish"]["a"] < result["finish"]["s"]
    assert "isolado" not in result["order"]


def test_dfs_deep_dag_is_iterative():
    graph = DirectedGraph()
    for i in range(1500):
        graph.add_edge(i, i + 1, 1)
    result = dfs(graph, 0)
    assert len(result["order"]) == 1501
    assert result["has_cycle"] is False


def test_dfs_self_loop_is_back_edge():
    graph = DirectedGraph()
    graph.add_edge("s", "s", 1)
    result = dfs(graph, "s")
    assert result["classification"] == [("s", "s", "retorno")]
    assert result["has_cycle"] is True
