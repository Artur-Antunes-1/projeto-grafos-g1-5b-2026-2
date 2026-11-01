# [IA] OpenAI Codex - geração integral da execução e dos relatórios da Parte 1.
"""Experimentos dos labirintos; resultados derivados do núcleo próprio."""
from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path

from .graphs.algorithms import bfs, dfs, dijkstra, bellman_ford, reconstruct_path
from .graphs.estados import build_state_graph, build_position_graph
from .graphs.io import read_map


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def write_csv(path, rows, fields=None):
    rows = list(rows)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with Path(path).open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def graph_metrics(graph, nodes=None):
    selected = set(graph.adj) if nodes is None else set(nodes)
    n = len(selected)
    m = sum(1 for u in selected for edge in graph.adj[u] if edge.target in selected)
    return {'order': n, 'size': m, 'density': m / (n * (n - 1)) if n > 1 else 0}


def _layer(state):
    return ''.join(sorted(state.keys)) or '-'


def _degrees(graph, nodes):
    incoming = Counter({node: 0 for node in nodes})
    outgoing = Counter({node: 0 for node in nodes})
    for u in nodes:
        for edge in graph.adj[u]:
            if edge.target in nodes:
                outgoing[u] += 1
                incoming[edge.target] += 1
    return incoming, outgoing


def _edge_cost(graph, source, target):
    return next(edge.weight for edge in graph.adj[source] if edge.target == target)


def _solution(graph, initial, states, algorithm):
    result = {'status': 'OK', 'path': [], 'steps': None, 'cost': None, 'trace': [], 'negative_cycle': []}
    try:
        search = {'BFS': bfs, 'DFS': dfs, 'DIJKSTRA': dijkstra, 'BELLMAN_FORD': bellman_ford}[algorithm](graph, initial)
    except ValueError as error:
        if algorithm != 'DIJKSTRA':
            raise
        result.update(status='RECUSA', reason=str(error))
        return result, None
    result['negative_cycle'] = search.get('negative_cycle', [])
    if 'ALVO' in search.get('affected', set()):
        result.update(status='CICLO_NEGATIVO', reason='Ciclo negativo alcançável pode atingir ALVO; não há custo mínimo finito.')
        return result, search
    reached = 'ALVO' in search.get('distance', search.get('discover', {}))
    if not reached or not math.isfinite(search.get('distance', {}).get('ALVO', 0)):
        result['status'] = 'SEM_SOLUCAO'
        return result, search
    path = reconstruct_path(search['parent'], initial, 'ALVO')
    if not path:
        result['status'] = 'SEM_SOLUCAO'
        return result, search
    cost = 0
    trace = []
    for index, label in enumerate(path):
        if index:
            cost += _edge_cost(graph, path[index - 1], label)
        if label in states:
            state = states[label]
            trace.append({'state': label, 'row': state.row, 'col': state.col, 'keys': sorted(state.keys), 'bonus': sorted(state.bonus), 'cost': cost})
    result.update(path=path, steps=max(0, len(trace) - 1), cost=cost, trace=trace)
    return result, search


def solve_maze(maze, consumable_source=False):
    graph, initial, states = build_state_graph(maze, consumable_source=consumable_source)
    solutions, searches = {}, {}
    for algorithm in ['BFS', 'DFS', 'DIJKSTRA', 'BELLMAN_FORD']:
        solutions[algorithm], searches[algorithm] = _solution(graph, initial, states, algorithm)
    backward = bfs(graph.transpose(), 'ALVO')
    reaches_target = {node for node, distance in backward['distance'].items() if math.isfinite(distance)}
    traps = sorted(set(states) - reaches_target)
    physical = set(states)
    incoming, outgoing = _degrees(graph, physical)
    multiplicity = Counter((s.row, s.col) for s in states.values())
    free = sum(cell != '#' for row in maze.rows for cell in row)
    bonuses = len(maze.bonus_positions) + (len(maze.source_positions) if consumable_source else 0)
    ceiling = free * 2 ** len(maze.keys) * 2 ** bonuses
    position_graph, _, _ = build_position_graph(maze)
    metrics = {
        'G_pos': graph_metrics(position_graph),
        'G_est': graph_metrics(graph, physical),
        'theoretical_ceiling': ceiling,
        'occupancy': len(states) / ceiling,
        'max_indegree_state': min(incoming, key=lambda label: (-incoming[label], label)),
        'max_outdegree_state': min(outgoing, key=lambda label: (-outgoing[label], label)),
        'max_indegree': max(incoming.values()),
        'max_outdegree': max(outgoing.values()),
        'max_multiplicity': max(multiplicity.values()),
        'max_multiplicity_cells': [list(pos) for pos, count in sorted(multiplicity.items()) if count == max(multiplicity.values())],
        'multiplicity': {f'{r},{c}': count for (r, c), count in sorted(multiplicity.items())},
        'dead_ends': sorted(label for label, state in states.items() if not outgoing[label] and maze.rows[state.row][state.col] != 'G'),
        'traps_count': len(traps),
        'traps_fraction': len(traps) / len(states),
        'metrics_exclude_ALVO': True,
    }
    layers = {}
    for key in sorted({_layer(state) for state in states.values()}):
        labels = {label for label, state in states.items() if _layer(state) == key}
        layers[key] = graph_metrics(graph, labels)
    crossings = Counter()
    for u in physical:
        for edge in graph.adj[u]:
            if edge.target in states and _layer(states[u]) != _layer(states[edge.target]):
                target = states[edge.target]
                crossings[(_layer(states[u]), _layer(target), target.row, target.col)] += 1
    payload = {
        'rows': list(maze.rows), 'initial': initial,
        'states': {label: {'row': state.row, 'col': state.col, 'keys': sorted(state.keys), 'bonus': sorted(state.bonus)} for label, state in states.items()},
        'edges': [{'source': u, 'target': edge.target, 'weight': edge.weight, 'movement': edge.movement, 'cell': edge.cell} for u, neighbors in graph.adj.items() for edge in neighbors],
        'solutions': solutions, 'traps': traps, 'metrics': metrics,
        'bfs_parent': searches['BFS']['parent'],
        'bfs_distance': {node: distance for node, distance in searches['BFS']['distance'].items() if math.isfinite(distance)},
        'layers': {'layers': layers, 'crossings': [{'from': a, 'to': b, 'row': r, 'col': c, 'count': count} for (a, b, r, c), count in sorted(crossings.items())]},
        'degrees': [{'estado': node, 'grau_entrada': incoming[node], 'grau_saida': outgoing[node]} for node in sorted(states)],
        'dfs_counts': dict(Counter(item[2] for item in searches['DFS']['classification'])),
        'dfs_classification': searches['DFS']['classification'],
    }
    return payload


def _position_solution(maze, doors):
    graph, initial, goals = build_position_graph(maze, doors=doors)
    search = bfs(graph, initial)
    reachable = [g for g in goals if math.isfinite(search['distance'][g])]
    if not reachable:
        return [], None
    target = min(reachable, key=lambda goal: (search['distance'][goal], goal))
    return reconstruct_path(search['parent'], initial, target), search['distance'][target]


def _is_valid_position_path(path, payload):
    if not path:
        return False
    current = payload['initial']
    adjacent = {}
    for edge in payload['edges']:
        adjacent.setdefault(edge['source'], []).append(edge['target'])
    for pos in path[1:]:
        choices = [label for label in adjacent.get(current, []) if label in payload['states'] and (payload['states'][label]['row'], payload['states'][label]['col']) == tuple(pos)]
        if not choices:
            return False
        current = choices[0]
    row, col = path[-1]
    return payload['rows'][row][col] == 'G'


def run_part1(root, out, render=True):
    root, out = Path(root), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    maps = sorted((root / 'data/mapas').glob('*.txt')) + sorted((root / 'data/mapas_grupo').glob('*.txt'))
    payload, comparisons, solution_rows, dfs_rows = {}, [], [], []
    for path in maps:
        maze = read_map(path)
        name = path.stem
        print(f'Parte 1: {name}', flush=True)
        item = solve_maze(maze)
        payload[name] = item
        write_csv(out / f'arestas_{name}.csv', ({'origem': e['source'], 'destino': e['target'], 'movimento': e['movement'], 'casa_destino': e['cell'], 'peso': e['weight']} for e in item['edges']), ['origem', 'destino', 'movimento', 'casa_destino', 'peso'])
        write_csv(out / f'graus_{name}.csv', item['degrees'])
        for algorithm, result in item['solutions'].items():
            solution_rows.append({'mapa': name, 'algoritmo': algorithm, 'passos': result['steps'], 'custo': result['cost'], 'status': result['status'], 'caminho': json.dumps(result['path'], ensure_ascii=False)})
        dfs_rows.append({'mapa': name, **{kind: item['dfs_counts'].get(kind, 0) for kind in ['arvore', 'retorno', 'avanco', 'cruzamento']}})
        if name.startswith(('m02', 'm03', 'm04')):
            for mode, description in [('floor', 'portas_como_chao'), ('wall', 'portas_como_parede')]:
                pos_path, steps = _position_solution(maze, mode)
                valid = _is_valid_position_path(pos_path, item)
                comparisons.append({'mapa': name, 'abordagem': description, 'passos': steps, 'caminho_valido': valid, 'observacao': 'Sem caminho nesta modelagem.' if not pos_path else ('Percurso respeita o jogo.' if valid else 'Percurso atravessa porta sem chave.'), 'caminho': json.dumps(pos_path)})
            result = item['solutions']['BFS']
            comparisons.append({'mapa': name, 'abordagem': 'grafo_estados', 'passos': result['steps'], 'caminho_valido': result['status'] == 'OK', 'observacao': result['status'], 'caminho': json.dumps(result['path'])})
        if name.startswith(('m04', 'm07')):
            prefix = name.split('_')[0]
            write_csv(out / f'armadilhas_{prefix}.csv', ({'estado': label} for label in item['traps']), ['estado'])
        if name.startswith(('m03', 'm08')):
            prefix = name.split('_')[0]
            write_json(out / f'percurso_{prefix}.json', item['solutions']['BELLMAN_FORD'])
        if name.startswith('m05'):
            pos_graph, initial, _ = build_position_graph(maze)
            search = bellman_ford(pos_graph, initial)
            cycle = search['negative_cycle']
            write_json(out / 'comparacao_bonus_m05.json', {'G_pos_cycle': cycle, 'G_pos_cycle_cost': sum(_edge_cost(pos_graph, a, b) for a, b in zip(cycle, cycle[1:])), 'G_est_cycle': item['solutions']['BELLMAN_FORD']['negative_cycle']})
        if name.startswith('m06'):
            cycle = item['solutions']['BELLMAN_FORD']['negative_cycle']
            weights = {(e['source'], e['target']): e['weight'] for e in item['edges']}
            write_json(out / 'ciclo_negativo_m06.json', {'cycle': cycle, 'cost': sum(weights[a, b] for a, b in zip(cycle, cycle[1:]))})
            fixed = solve_maze(maze, consumable_source=True)
            payload['m06_fonte_consumivel'] = fixed
            write_json(out / 'fonte_consumivel_m06.json', {'rule': 'Primeira entrada em cada fonte custa -2; seguintes custam 1.', 'metrics': fixed['metrics'], 'solution': fixed['solutions']['BELLMAN_FORD']})
    write_csv(out / 'solucoes.csv', solution_rows)
    write_csv(out / 'dfs_classificacao.csv', dfs_rows)
    write_csv(out / 'comparacao_modelagem.csv', comparisons)
    write_json(out / 'metricas_global.json', {name: item['metrics'] for name, item in payload.items()})
    write_json(out / 'camadas.json', {name: item['layers'] for name, item in payload.items()})
    write_json(out / 'resultados.json', payload)
    group = {name: {'states': item['metrics']['G_est']['order'], 'arcs_without_ALVO': item['metrics']['G_est']['size'], 'arcs_with_ALVO': len(item['edges']), 'BFS': item['solutions']['BFS']['steps'], 'minimum_cost': item['solutions']['BELLMAN_FORD']['cost'], 'traps_fraction': item['metrics']['traps_fraction']} for name, item in payload.items() if name.startswith('g1_')}
    write_json(out / 'gabarito_mapas_grupo.json', group)
    first = payload.get('g1_01_tres_desvios')
    if first:
        trace = first['solutions']['BELLMAN_FORD']['trace']
        assert set('abc') <= set(trace[-1]['keys'])
        assert any(first['rows'][step['row']][step['col']] == '+' for step in trace)
        assert any(first['rows'][step['row']][step['col']] in '><^v' for step in trace)
    if 'g1_02_queda_sem_volta' in payload:
        assert payload['g1_02_queda_sem_volta']['metrics']['traps_fraction'] >= .2
    if render:
        from .viz import render_part1
        render_part1(payload, out)
    return payload
