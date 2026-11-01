# [IA] OpenAI Codex - geração assistida de testes de estados com contagens manuais.
from math import inf

import pytest

from src.graphs.algorithms import bellman_ford, bfs
from src.graphs.estados import ALVO, State, build_position_graph, build_state_graph
from src.graphs.io import parse_map


def test_state_label_sorts_keys_and_bonus_indices():
    assert State(3, 5, frozenset({"b", "a"}), frozenset({2, 0})).label() == "(3,5)|ab|{0,2}"
    assert State(1, 1, frozenset(), frozenset()).label() == "(1,1)|-|{}"


def test_minimum_key_map_has_five_physical_states_and_seven_arcs_by_hand():
    # Corredor S-a-A-G: S0->a1; a1->A1,S1; A1->G1,a1; S1->a1;
    # G1->ALVO. São cinco estados físicos e sete arcos, seis físicos.
    maze = parse_map("######\n#SaAG#\n######")
    graph, start, states = build_state_graph(maze)
    assert len(states) == 5
    assert len(graph) == 6
    assert len(list(graph.edges())) == 7
    assert start == "(1,1)|-|{}"
    assert "(1,1)|a|{}" in states
    assert graph.adj["(1,4)|a|{}"][0].target == ALVO
    assert graph.adj["(1,4)|a|{}"][0].weight == 0
    assert graph.adj[ALVO] == []
    assert bfs(graph, start)["distance"][ALVO] == 4


def test_neighbor_order_and_goal_is_terminal():
    maze = parse_map(".G.\n.S.\n...")
    graph, start, states = build_state_graph(maze)
    assert [edge.movement for edge in graph.adj[start]] == ["N", "L", "S", "O"]
    goal_labels = [label for label, state in states.items() if (state.row, state.col) in maze.goals]
    assert all(len(graph.adj[label]) == 1 and graph.adj[label][0].target == ALVO for label in goal_labels)


def test_conveyor_into_wall_has_no_exit_and_no_target_path():
    maze = parse_map("#####\n#S>##\n###G#\n#####")
    graph, start, states = build_state_graph(maze)
    assert graph.adj["(1,2)|-|{}"] == []
    assert bfs(graph, start)["distance"][ALVO] == inf
    assert set(states) == {"(1,1)|-|{}", "(1,2)|-|{}"}


def test_bonus_is_consumed_once_and_eliminates_position_negative_cycle():
    maze = parse_map("#####\n#S+G#\n#####")
    graph, start, states = build_state_graph(maze)
    assert len(states) == 4
    assert len(list(graph.edges())) == 5
    assert graph.adj[start][0].weight == -4
    assert graph.adj["(1,1)|-|{0}"][0].weight == 1
    result = bellman_ford(graph, start)
    assert result["distance"][ALVO] == -3
    assert result["negative_cycle"] == []
    positions, pstart, _ = build_position_graph(maze)
    assert bellman_ford(positions, pstart)["negative_cycle"]


def test_source_consumable_uses_indices_after_bonus_and_removes_negative_cycle():
    maze = parse_map("######\n#S*+G#\n######")
    graph, start, states = build_state_graph(maze)
    assert bellman_ford(graph, start)["distance"][ALVO] == -inf
    fixed, initial, fixed_states = build_state_graph(maze, consumable_source=True)
    assert fixed.adj[initial][0].weight == -2
    assert fixed.adj[initial][0].target == "(1,2)|-|{1}"
    assert fixed.adj["(1,1)|-|{1}"][0].weight == 1
    assert "(1,3)|-|{0,1}" in fixed_states
    result = bellman_ford(fixed, initial)
    assert result["negative_cycle"] == []
    assert result["distance"][ALVO] == -5


def test_position_graph_door_policy_and_terminal_goals():
    maze = parse_map("SAG")
    floor, source, goals = build_position_graph(maze, doors="floor")
    wall, _, _ = build_position_graph(maze, doors="wall")
    assert source == (0, 0) and goals == ((0, 2),)
    assert bfs(floor, source)["distance"][(0, 2)] == 2
    assert (0, 1) not in wall.adj
    assert floor.adj[(0, 2)] == []
    state_graph, initial, _ = build_state_graph(maze)
    assert bfs(state_graph, initial)["distance"][ALVO] == inf
    with pytest.raises(ValueError, match="doors"):
        build_position_graph(maze, doors="invalid")
