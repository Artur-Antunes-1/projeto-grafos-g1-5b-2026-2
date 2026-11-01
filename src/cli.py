# [IA] OpenAI Codex - geração integral da interface de linha de comando.
"""Entrada única dos experimentos reproduzíveis."""
import argparse
import json
import math
import sys
from pathlib import Path

from .graphs.algorithms import bfs, dfs, dijkstra, bellman_ford, reconstruct_path
from .graphs.io import read_map
from .parte1 import solve_maze, run_part1, write_json, write_csv

ROOT = Path(__file__).resolve().parents[1]


def parser():
    command = argparse.ArgumentParser(description='Teoria dos Grafos - G1 / turma 5B')
    mode = command.add_mutually_exclusive_group(required=True)
    mode.add_argument('--all', action='store_true', help='Gerar as duas partes e o relatório técnico.')
    mode.add_argument('--mapa', type=Path, help='Resolver um mapa TXT.')
    mode.add_argument('--dataset', type=Path, help='CSV ou pasta com Bitcoin Alpha.')
    mode.add_argument('--report', action='store_true', help='Regenerar PDFs e Markdown dos resultados existentes.')
    command.add_argument('--alg', type=str.upper, choices=['BFS', 'DFS', 'DIJKSTRA', 'BELLMAN_FORD'], default='BFS')
    command.add_argument('--source', help='ID da origem na Parte 2.')
    command.add_argument('--target', help='ID do destino na Parte 2.')
    command.add_argument('--out', type=Path, help='Pasta de saída; com --all, recebe parte1/ e parte2/.')
    command.add_argument('--benchmark', action='store_true', help='Executar os experimentos completos da Parte 2.')
    command.add_argument('--repeticoes', type=int, default=5, help='Repetições por tarefa de benchmark, mínimo 5.')
    command.add_argument('--fonte-consumivel', action='store_true', help='Fonte * custa -2 na primeira entrada e 1 depois.')
    command.add_argument('--interactive', action='store_true', help='Gerar HTML offline para o mapa.')
    command.add_argument('--armadilhas', action='store_true', help='Exportar estados que não alcançam a saída.')
    command.add_argument('--no-render', action='store_true', help='Gerar apenas os dados, sem gráficos/PDF.')
    return command


def _safe_distance(value):
    return value if math.isfinite(value) else ('-infinito' if value < 0 else 'inalcancavel')


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.repeticoes < 5:
            raise ValueError('--repeticoes deve ser pelo menos 5.')
        if args.all:
            base = args.out or ROOT / 'out'
            run_part1(ROOT, base / 'parte1', render=not args.no_render)
            from .parte2 import run_part2
            run_part2(ROOT, base / 'parte2', repetitions=args.repeticoes, render=not args.no_render)
            if not args.no_render:
                from .report import generate_reports
                generate_reports(ROOT, base)
            return 0
        if args.report:
            from .report import generate_reports
            generate_reports(ROOT, args.out or ROOT / 'out')
            return 0
        if args.mapa:
            out = args.out or ROOT / 'out/parte1'
            out.mkdir(parents=True, exist_ok=True)
            maze = read_map(args.mapa)
            result = solve_maze(maze, consumable_source=args.fonte_consumivel)
            name = f'{maze.name}_consumivel' if args.fonte_consumivel else maze.name
            solution = result['solutions'][args.alg]
            write_json(out / f'solucao_{name}_{args.alg}.json', solution)
            write_csv(out / f'arestas_{name}.csv', ({'origem': e['source'], 'destino': e['target'], 'movimento': e['movement'], 'casa_destino': e['cell'], 'peso': e['weight']} for e in result['edges']), ['origem', 'destino', 'movimento', 'casa_destino', 'peso'])
            if args.armadilhas:
                write_csv(out / f'armadilhas_{name}.csv', ({'estado': label} for label in result['traps']), ['estado'])
            if args.interactive:
                from .viz import render_part1
                render_part1({name: result}, out)
            print(json.dumps({'mapa': name, **{key: solution[key] for key in ['status', 'steps', 'cost']}, 'armadilhas': len(result['traps'])}, ensure_ascii=False))
            return 0
        if not args.source and not args.benchmark:
            raise ValueError('Informe --source para executar um algoritmo no dataset, ou use --benchmark.')
        from .parte2 import load_dataset, make_graph, run_part2
        out = args.out or ROOT / 'out/parte2'
        dataset_file = args.dataset / 'bitcoinalpha.csv' if args.dataset.is_dir() else args.dataset
        if args.benchmark:
            run_part2(ROOT, out, repetitions=args.repeticoes, render=not args.no_render, dataset=dataset_file)
            return 0
        records = load_dataset(dataset_file)
        graph = make_graph(records, transform='10-rating' if args.alg == 'DIJKSTRA' else 'rating')
        def node(text):
            candidate = int(text)
            if candidate not in graph.adj:
                raise ValueError(f'Usuário {candidate} não está no dataset.')
            return candidate
        source = node(args.source)
        target = node(args.target) if args.target is not None else None
        result = {'BFS': bfs, 'DFS': dfs, 'DIJKSTRA': dijkstra, 'BELLMAN_FORD': bellman_ford}[args.alg](graph, source)
        cycle = result.get('negative_cycle', [])
        distance = result.get('distance', {})
        has_relevant_cycle = bool(cycle) if target is None else target in result.get('affected', set())
        status = 'CICLO_NEGATIVO' if has_relevant_cycle else 'OK'
        if target is not None:
            reached = target in result.get('discover', {}) if args.alg == 'DFS' else math.isfinite(distance[target])
            if not reached and status != 'CICLO_NEGATIVO':
                status = 'SEM_SOLUCAO'
        exported = {'algorithm': args.alg, 'source': source, 'target': target, 'status': status, 'weight_model': '10-rating' if args.alg == 'DIJKSTRA' else 'rating', 'distance': {str(k): _safe_distance(v) for k, v in distance.items()}, 'order': result.get('order', []), 'negative_cycle': cycle, 'path': reconstruct_path(result['parent'], source, target) if target is not None and status == 'OK' else []}
        write_json(out / f'consulta_{args.alg}_{source}.json', exported)
        print(json.dumps({key: exported[key] for key in ['algorithm', 'source', 'target', 'status', 'weight_model']}, ensure_ascii=False))
        return 0
    except (ValueError, OSError) as error:
        print(f'Erro: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
