# [IA] OpenAI Codex - geração assistida de testes da representação dirigida.
from src.graphs.graph import DirectedGraph, Edge


def test_graph_preserves_direction_order_metadata_and_isolated_nodes():
    graph = DirectedGraph()
    graph.add_node("isolado")
    graph.add_edge("s", "a", 3, "N", ",")
    graph.add_edge("s", "b", -2, "L", "*")
    assert len(graph) == 4
    assert graph.adj["s"] == [Edge("a", 3, "N", ","), Edge("b", -2, "L", "*")]
    assert graph.adj["a"] == []
    assert list(graph.edges()) == [("s", "a", 3), ("s", "b", -2)]
    transposed = graph.transpose()
    assert set(transposed.adj) == set(graph.adj)
    assert transposed.adj["a"] == [Edge("s", 3, "N", ",")]
    assert list(transposed.transpose().edges()) == list(graph.edges())


def test_graph_preserves_parallel_edges_and_self_loops():
    graph = DirectedGraph()
    graph.add_edge(1, 1, 0)
    graph.add_edge(1, 2, 1)
    graph.add_edge(1, 2, 2)
    assert list(graph.edges()) == [(1, 1, 0), (1, 2, 1), (1, 2, 2)]
