# [IA] OpenAI Codex - geração assistida da representação de grafo dirigido.
"""Lista de adjacência dirigida que conserva a ordem de inserção dos arcos."""

from collections.abc import Hashable, Iterator
from dataclasses import dataclass

Node = Hashable
Weight = int | float


@dataclass(frozen=True, slots=True)
class Edge:
    """Arco de saída; movimento e casa são metadados opcionais do labirinto."""

    target: Node
    weight: Weight
    movement: str = ""
    cell: str = ""


class DirectedGraph:
    """Grafo com nós hashable; aceita laços e arcos paralelos sem espelhá-los."""

    def __init__(self) -> None:
        self.adj: dict[Node, list[Edge]] = {}

    def add_node(self, node: Node) -> None:
        self.adj.setdefault(node, [])

    def add_edge(
        self, source: Node, target: Node, weight: Weight,
        movement: str = "", cell: str = "",
    ) -> None:
        self.add_node(source)
        self.add_node(target)
        self.adj[source].append(Edge(target, weight, movement, cell))

    def edges(self) -> Iterator[tuple[Node, Node, Weight]]:
        for source, edges in self.adj.items():
            for edge in edges:
                yield source, edge.target, edge.weight

    def transpose(self) -> "DirectedGraph":
        result = DirectedGraph()
        for node in self.adj:
            result.add_node(node)
        for source, edges in self.adj.items():
            for edge in edges:
                result.add_edge(edge.target, source, edge.weight, edge.movement, edge.cell)
        return result

    def __len__(self) -> int:
        return len(self.adj)
