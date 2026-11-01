# [IA] OpenAI Codex - geração assistida de oráculos independentes de integração.
"""NetworkX fica restrito a testes, como permite o enunciado."""
from math import inf
from random import Random

import networkx as nx
import pytest

from src.graphs.algorithms import bellman_ford, bfs, dfs, dijkstra, reconstruct_path
from src.graphs.graph import DirectedGraph
from src.graphs.io import parse_map
from src.parte1 import solve_maze


@pytest.mark.parametrize("seed", range(8))
def test_nonnegative_graphs_match_networkx_from_multiple_sources(seed):
    random = Random(seed)
    graph, oracle = DirectedGraph(), nx.DiGraph()
    for node in range(12):
        graph.add_node(node)
        oracle.add_node(node)
    for u in range(12):
        for v in range(12):
            if random.random() < 0.16:
                weight = random.randrange(0, 15)
                graph.add_edge(u, v, weight)
                oracle.add_edge(u, v, weight=weight)
    for source in [0, 4, 11]:
        expected_bfs = nx.single_source_shortest_path_length(oracle, source)
        expected_weighted = nx.single_source_dijkstra_path_length(oracle, source)
        searches = [bfs(graph, source), dijkstra(graph, source), bellman_ford(graph, source)]
        assert searches[0]["order"] == list(nx.bfs_tree(oracle, source))
        assert dfs(graph, source)["order"] == list(nx.dfs_preorder_nodes(oracle, source))
        for result, expected in zip(searches, [expected_bfs, expected_weighted, expected_weighted]):
            assert result["distance"] == {node: expected.get(node, inf) for node in graph.adj}
            for target, distance in result["distance"].items():
                path = reconstruct_path(result["parent"], source, target)
                assert bool(path) == (distance != inf)
                if path:
                    assert path[0] == source and path[-1] == target
                    assert all(oracle.has_edge(u, v) for u, v in zip(path, path[1:]))


@pytest.mark.parametrize("seed", range(8))
def test_signed_dags_match_networkx_without_negative_cycles(seed):
    random = Random(seed)
    graph, oracle = DirectedGraph(), nx.DiGraph()
    for node in range(15):
        graph.add_node(node)
        oracle.add_node(node)
    for u in range(15):
        for v in range(u + 1, 15):
            if random.random() < 0.24:
                weight = random.randrange(-8, 12)
                graph.add_edge(u, v, weight)
                oracle.add_edge(u, v, weight=weight)
    for source in [0, 5, 14]:
        result = bellman_ford(graph, source)
        expected = nx.single_source_bellman_ford_path_length(oracle, source)
        assert result["distance"] == {node: expected.get(node, inf) for node in graph.adj}
        assert result["negative_cycle"] == []
        assert result["affected"] == set()
        assert dfs(graph, source)["has_cycle"] is False


@pytest.mark.parametrize("text", [
    "SGG",
    "S+G",
    "#########\n#SG######\n#v#######\n#.*######\n#########",
    "#######\n#S#..G#\n#######",
])
def test_part1_metrics_traps_and_steps_match_independent_graph_oracle(text):
    payload = solve_maze(parse_map(text))
    oracle = nx.DiGraph()
    oracle.add_nodes_from([*payload["states"], "ALVO"])
    oracle.add_weighted_edges_from((edge["source"], edge["target"], edge["weight"]) for edge in payload["edges"])
    physical = oracle.subgraph(payload["states"])
    metrics = payload["metrics"]["G_est"]
    assert metrics["order"] == physical.number_of_nodes()
    assert metrics["size"] == physical.number_of_edges()
    assert metrics["density"] == nx.density(physical)
    reaches_target = nx.ancestors(oracle, "ALVO")
    assert set(payload["traps"]) == set(payload["states"]) - reaches_target
    degree_rows = {row["estado"]: row for row in payload["degrees"]}
    for node in physical:
        assert degree_rows[node]["grau_entrada"] == physical.in_degree(node)
        assert degree_rows[node]["grau_saida"] == physical.out_degree(node)
    for solution in payload["solutions"].values():
        if solution["status"] == "OK":
            assert solution["path"][-1] == "ALVO"
            assert solution["steps"] == len(solution["trace"]) - 1 == len(solution["path"]) - 2
            assert all(step["state"] != "ALVO" for step in solution["trace"])
            assert solution["cost"] == sum(oracle[u][v]["weight"] for u, v in zip(solution["path"], solution["path"][1:]))


def test_negative_cycle_in_trap_does_not_invalidate_a_finite_target_solution():
    payload = solve_maze(parse_map("#########\n#SG######\n#v#######\n#.*######\n#########"))
    solution = payload["solutions"]["BELLMAN_FORD"]
    assert solution["negative_cycle"]
    assert solution["status"] == "OK"
    assert solution["cost"] == 1
    assert solution["steps"] == 1
    assert set(payload["traps"]) == {"(2,1)|-|{}", "(3,1)|-|{}", "(3,2)|-|{}"}
