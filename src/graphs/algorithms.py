# [IA] OpenAI Codex - geração assistida de BFS, DFS, Dijkstra e Bellman-Ford próprios.
"""Algoritmos próprios sobre listas de adjacência, sem bibliotecas de grafos."""

from collections import deque
from collections.abc import Hashable, Mapping
from heapq import heappop, heappush
from itertools import count
from math import inf

from .graph import DirectedGraph, Node


def _require_source(graph: DirectedGraph, source: Node) -> None:
    if source not in graph.adj:
        raise ValueError(f"Origem {source!r} não pertence ao grafo.")


def reconstruct_path(parent: Mapping, source: Hashable, target: Hashable) -> list:
    """Retorna [] para alvo inalcançável, cadeia incompleta ou cadeia cíclica."""
    if source not in parent or target not in parent:
        return []
    path = []
    seen = set()
    current = target
    while current != source:
        if current in seen or current not in parent:
            return []
        seen.add(current)
        path.append(current)
        current = parent[current]
    path.append(source)
    path.reverse()
    return path


def bfs(graph: DirectedGraph, source: Node) -> dict:
    """Busca iterativa em largura; distância conta arcos e ignora os pesos."""
    _require_source(graph, source)
    distance = dict.fromkeys(graph.adj, inf)
    # Ausência da chave identifica vértice inalcançável; None pode ser um nó.
    parent = {source: None}
    distance[source] = 0
    queue = deque([source])
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for edge in graph.adj[node]:
            target = edge.target
            if distance[target] == inf:
                distance[target] = distance[node] + 1
                parent[target] = node
                queue.append(target)
    return {"distance": distance, "parent": parent, "order": order}


def dfs(graph: DirectedGraph, source: Node) -> dict:
    """DFS iterativa equivalente à recursiva, respeitando a ordem da adjacência.

    Classifica somente arcos alcançáveis da fonte. As cores 0/1/2 representam
    vértices não descobertos, ativos na pilha e já finalizados.
    """
    _require_source(graph, source)
    color = dict.fromkeys(graph.adj, 0)
    parent = {source: None}
    discover = {}
    finish = {}
    order = [source]
    classification = []
    has_cycle = False
    time = 1
    color[source] = 1
    discover[source] = time
    stack = [(source, iter(graph.adj[source]))]
    while stack:
        node, neighbors = stack[-1]
        edge = next(neighbors, None)
        if edge is None:
            stack.pop()
            color[node] = 2
            time += 1
            finish[node] = time
            continue
        target = edge.target
        if color[target] == 0:
            classification.append((node, target, "arvore"))
            parent[target] = node
            color[target] = 1
            time += 1
            discover[target] = time
            order.append(target)
            stack.append((target, iter(graph.adj[target])))
        elif color[target] == 1:
            classification.append((node, target, "retorno"))
            has_cycle = True
        elif discover[node] < discover[target]:
            classification.append((node, target, "avanco"))
        else:
            classification.append((node, target, "cruzamento"))
    return {
        "parent": parent, "order": order, "discover": discover, "finish": finish,
        "classification": classification, "has_cycle": has_cycle,
    }


def dijkstra(graph: DirectedGraph, source: Node) -> dict:
    """Caminhos mínimos para pesos não negativos; recusa o grafo inteiro."""
    _require_source(graph, source)
    if any(weight < 0 for _, _, weight in graph.edges()):
        raise ValueError("Dijkstra recusa grafos com qualquer arco de peso negativo.")
    distance = dict.fromkeys(graph.adj, inf)
    parent = {source: None}
    distance[source] = 0
    sequence = count()
    heap = [(0, next(sequence), source)]
    while heap:
        cost, _, node = heappop(heap)
        if cost != distance[node]:
            continue
        for edge in graph.adj[node]:
            candidate = cost + edge.weight
            if candidate < distance[edge.target]:
                distance[edge.target] = candidate
                parent[edge.target] = node
                heappush(heap, (candidate, next(sequence), edge.target))
    return {"distance": distance, "parent": parent, "negative_cycle": [], "affected": set()}


def bellman_ford(graph: DirectedGraph, source: Node) -> dict:
    """Bellman-Ford com até |V|-1 passadas e parada se nenhuma aresta relaxar.

    Uma passada adicional detecta ciclos negativos alcançáveis. Todos os nós
    alcançáveis desses ciclos têm distância -inf; componentes inacessíveis à
    fonte conservam inf. O ciclo devolvido é dirigido e fechado.
    """
    _require_source(graph, source)
    nodes = list(graph.adj)
    indices = {node: index for index, node in enumerate(nodes)}
    size = len(nodes)
    # A lista fica pronta uma vez; o laço O(VE) usa índices inteiros e listas.
    edges = [(indices[u], indices[v], weight) for u, v, weight in graph.edges()]
    distance = [inf] * size
    parent = [-1] * size
    distance[indices[source]] = 0
    for _ in range(size - 1):
        changed = False
        for u, v, weight in edges:
            candidate = distance[u] + weight
            if candidate < distance[v]:
                distance[v] = candidate
                parent[v] = u
                changed = True
        if not changed:
            break

    seeds = set()
    last = -1
    for u, v, weight in edges:
        candidate = distance[u] + weight
        if candidate < distance[v]:
            distance[v] = candidate
            parent[v] = u
            seeds.add(v)
            last = v

    cycle = []
    if last != -1:
        vertex = last
        # Após |V| predecessores, estamos dentro de um ciclo, não na cauda.
        for _ in range(size):
            vertex = parent[vertex]
        cycle_indices = [vertex]
        current = parent[vertex]
        while current != vertex:
            cycle_indices.append(current)
            current = parent[current]
        cycle_indices.append(vertex)
        cycle = [nodes[index] for index in reversed(cycle_indices)]

    affected = {nodes[index] for index in seeds}
    queue = deque(affected)
    while queue:
        node = queue.popleft()
        for edge in graph.adj[node]:
            if edge.target not in affected:
                affected.add(edge.target)
                queue.append(edge.target)
    result_distance = {node: distance[index] for index, node in enumerate(nodes)}
    result_parent = {
        node: None if parent[index] == -1 else nodes[parent[index]]
        for index, node in enumerate(nodes)
        if distance[index] != inf and node not in affected
    }
    for node in affected:
        result_distance[node] = -inf
        # Não existe árvore de caminhos mínimos para esses vértices.
    return {
        "distance": result_distance, "parent": result_parent,
        "negative_cycle": cycle, "affected": affected,
    }
