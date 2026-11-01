# [IA] OpenAI Codex - geração assistida da construção própria dos grafos de estados e posições.
"""Modelagens dirigidas do labirinto; apenas estados alcançáveis são gerados."""

from collections import deque
from dataclasses import dataclass

from .graph import DirectedGraph
from .io import Maze

ALVO = "ALVO"
DIRECTIONS = (("N", -1, 0), ("L", 0, 1), ("S", 1, 0), ("O", 0, -1))
CONVEYORS = {"^": "N", ">": "L", "v": "S", "<": "O"}
ENTRY_COST = {",": 3, "~": 5, "+": -4, "*": -2}


@dataclass(frozen=True, slots=True)
class State:
    row: int
    col: int
    keys: frozenset[str] = frozenset()
    bonus: frozenset[int] = frozenset()

    def label(self) -> str:
        keys = "".join(sorted(self.keys)) or "-"
        bonus = ",".join(str(index) for index in sorted(self.bonus))
        return f"({self.row},{self.col})|{keys}|{{{bonus}}}"


def _neighbors(maze: Maze, row: int, col: int):
    symbol = maze.rows[row][col]
    if symbol == "G":
        return
    forced = CONVEYORS.get(symbol)
    height, width = len(maze.rows), len(maze.rows[0])
    for movement, dr, dc in DIRECTIONS:
        if forced is not None and movement != forced:
            continue
        nr, nc = row + dr, col + dc
        if 0 <= nr < height and 0 <= nc < width and maze.rows[nr][nc] != "#":
            yield nr, nc, movement, maze.rows[nr][nc]


def build_position_graph(maze: Maze, doors: str = "floor") -> tuple:
    """Grafo geométrico ingênuo; '+' sempre -4 e '*' sempre -2.

    Todas as casas livres entram, mesmo as inacessíveis a partir de S.
    Portas viram chão ou parede; G é terminal e não há nó virtual.
    """
    if doors not in {"floor", "wall"}:
        raise ValueError("doors deve ser 'floor' ou 'wall'.")
    graph = DirectedGraph()
    for row, line in enumerate(maze.rows):
        for col, symbol in enumerate(line):
            if symbol != "#" and not (doors == "wall" and symbol in "ABCD"):
                graph.add_node((row, col))
    for row, col in graph.adj:
        for nr, nc, movement, symbol in _neighbors(maze, row, col):
            if (nr, nc) in graph.adj:
                graph.add_edge((row, col), (nr, nc), ENTRY_COST.get(symbol, 1), movement, symbol)
    return graph, maze.start, maze.goals


def build_state_graph(maze: Maze, consumable_source: bool = False) -> tuple:
    """Explora por BFS as memórias de chaves e bônus, sem produto cartesiano.

    Consumir '+' dá -4 na primeira entrada, depois 1. No modo opcional,
    consumir '*' dá -2, depois 1; seus índices vêm após todos os '+'.
    """
    graph = DirectedGraph()
    initial_state = State(*maze.start)
    initial_label = initial_state.label()
    states = {initial_label: initial_state}
    labels = {initial_state: initial_label}
    graph.add_node(initial_label)
    graph.add_node(ALVO)
    queue = deque([initial_state])
    consumables = {position: index for index, position in enumerate(maze.bonus_positions)}
    if consumable_source:
        offset = len(maze.bonus_positions)
        consumables.update({position: offset + index for index, position in enumerate(maze.source_positions)})

    while queue:
        state = queue.popleft()
        label = labels[state]
        if maze.rows[state.row][state.col] == "G":
            graph.add_edge(label, ALVO, 0)
            continue
        for row, col, movement, symbol in _neighbors(maze, state.row, state.col):
            if symbol in "ABCD" and symbol.lower() not in state.keys:
                continue
            keys = state.keys | {symbol} if symbol in "abcd" else state.keys
            bonus = state.bonus
            weight = ENTRY_COST.get(symbol, 1)
            index = consumables.get((row, col))
            if index is not None:
                if index in bonus:
                    weight = 1
                else:
                    bonus = bonus | {index}
            target = State(row, col, keys, bonus)
            target_label = labels.get(target)
            if target_label is None:
                target_label = target.label()
                labels[target] = target_label
                states[target_label] = target
                graph.add_node(target_label)
                queue.append(target)
            graph.add_edge(label, target_label, weight, movement, symbol)
    return graph, initial_label, states
