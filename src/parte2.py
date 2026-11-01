# [IA] OpenAI Codex - implementação, experimentos e análise integralmente assistidos.
"""Experimentos reproduzíveis sobre avaliações dirigidas Bitcoin Alpha.

Os ratings são avaliações, não preços nem probabilidades. Somar ratings negativos
e minimizá-los acumula desconfiança; não representa confiança transitiva. O modelo
de Dijkstra, 10-rating por arco, responde a outra pergunta e cobra por cada arco.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import random
import statistics
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.graphs.algorithms import bellman_ford, bfs, dfs, dijkstra, reconstruct_path
from src.graphs.graph import DirectedGraph

RECEIVED_CSV_SHA256 = "d2f121d67f325ba2dfbbf0e9708843d7c9b0f898494957fb6b1b239db5150c8a"


@dataclass(frozen=True)
class Rating:
    source: int
    target: int
    rating: int
    timestamp: int


def _utc(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()


def read_ratings(path):
    """Lê sem modificar o CSV e rejeita dados ausentes/fora do domínio."""
    path = Path(path)
    records = []
    columns = ("SOURCE", "TARGET", "RATING", "TIME")
    missing = dict.fromkeys(columns, 0)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not set(columns).issubset(reader.fieldnames or []):
            raise ValueError(f"Cabeçalho deve conter {columns}")
        for line, row in enumerate(reader, start=2):
            for column in columns:
                missing[column] += int(not str(row.get(column) or "").strip())
            if any(not str(row.get(c) or "").strip() for c in columns):
                raise ValueError(f"Valor ausente na linha {line}; nenhum registro foi descartado.")
            try:
                source, target, rating, timestamp = (int(row[c]) for c in columns)
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Inteiro inválido na linha {line}") from exc
            if not -10 <= rating <= 10:
                raise ValueError(f"RATING fora do intervalo -10 a 10 na linha {line}")
            records.append(Rating(source, target, rating, timestamp))
    if not records:
        raise ValueError("Dataset vazio")
    nodes = {r.source for r in records} | {r.target for r in records}
    pairs = Counter((r.source, r.target) for r in records)
    signs = Counter("negative" if r.rating < 0 else "positive" if r.rating > 0 else "zero" for r in records)
    monthly_counts = Counter(datetime.fromtimestamp(r.timestamp, timezone.utc).strftime("%Y-%m") for r in records)
    peak_month, peak_count = max(monthly_counts.items(), key=lambda item: (item[1], item[0]))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    known_received = digest == RECEIVED_CSV_SHA256
    if known_received:
        version_note = (f"CSV recebido reconhecido pelo SHA-256: {len(records)} registros/{len(nodes)} usuários; "
                        "SNAP original tem 24186/3783. A comparação desta cópia foi documentada; "
                        "não foi reinserido o registro ausente.")
    else:
        version_note = (f"Versão não comparada à SNAP: {len(records)} registros/{len(nodes)} usuários. "
                        "O hash difere da cópia recebida previamente verificada; "
                        "não se afirma diferença de registros em relação à versão original.")
    return records, {
        "file": str(path), "sha256": digest, "is_known_received_csv": known_received,
        "rows": len(records), "nodes": len(nodes), "directed": True,
        "missing_by_column": missing,
        "sign_counts": {key: signs[key] for key in ("negative", "zero", "positive")},
        "rating_counts": dict(sorted(Counter(r.rating for r in records).items())),
        "rating_min": min(r.rating for r in records), "rating_max": max(r.rating for r in records),
        "rating_mean": statistics.mean(r.rating for r in records),
        "rating_median": statistics.median(r.rating for r in records),
        "time_min_utc": _utc(min(r.timestamp for r in records)),
        "time_max_utc": _utc(max(r.timestamp for r in records)),
        "monthly_counts_utc": dict(sorted(monthly_counts.items())),
        "monthly_peak_utc": {"month": peak_month, "count": peak_count},
        "duplicate_directed_pairs": sum(n - 1 for n in pairs.values()),
        "self_loops": sum(r.source == r.target for r in records),
        "source_url": "https://snap.stanford.edu/data/soc-sign-bitcoin-alpha.html",
        "version_note": version_note,
        "field_semantics": {"SOURCE": "quem avaliou", "TARGET": "quem recebeu a avaliação", "RATING": "-10 desconfiança total; +10 confiança total", "TIME": "segundos Unix; agregações temporais em UTC"},
    }


def build_rating_graph(records, transformed=False):
    graph = DirectedGraph()
    for node in sorted({r.source for r in records} | {r.target for r in records}):
        graph.add_node(node)
    for record in records:
        graph.add_edge(record.source, record.target, 10 - record.rating if transformed else record.rating)
    return graph


def load_dataset(path):
    """Adaptador de leitura simples para a CLI; metadados completos em read_ratings."""
    return read_ratings(path)[0]


def make_graph(records, transform="rating"):
    """Adaptador CLI com nomes explícitos dos dois objetivos documentados."""
    if transform not in ("rating", "10-rating"):
        raise ValueError("transform deve ser 'rating' ou '10-rating'")
    return build_rating_graph(records, transformed=transform == "10-rating")


def transform_graph(graph):
    result = DirectedGraph()
    for node in graph.adj:
        result.add_node(node)
    for source, target, weight in graph.edges():
        result.add_edge(source, target, 10 - weight)
    return result


def path_weight(graph, path):
    cost = 0
    for source, target in zip(path, path[1:]):
        matches = [edge.weight for edge in graph.adj[source] if edge.target == target]
        if not matches:
            raise ValueError(f"Não existe arco {source}->{target}")
        cost += min(matches)
    return cost


def select_sources(graph):
    """Maior saída, maior número de saídas negativas e saída mediana; desempate ID."""
    nodes = list(graph.adj)
    if not nodes:
        return []
    by_degree = sorted(nodes, key=lambda n: (-len(graph.adj[n]), n))
    by_negative = sorted(nodes, key=lambda n: (-sum(e.weight < 0 for e in graph.adj[n]), -len(graph.adj[n]), n))
    nonzero = [n for n in by_degree if graph.adj[n]]
    candidates = [by_degree[0], by_negative[0], (nonzero or by_degree)[len(nonzero or by_degree) // 2]] + by_degree
    sources = []
    for node in candidates:
        if node not in sources:
            sources.append(node)
        if len(sources) == min(3, len(nodes)):
            break
    return sources


def increasing_layer_dag(graph, source):
    """Controle acíclico: somente arcos reais que avançam estritamente nas camadas BFS.

    Todos os vértices alcançáveis e os arcos da árvore BFS são preservados.
    A retirada de retornos é uma intervenção experimental explicitamente declarada.
    """
    result = bfs(graph, source)
    layers = {n: d for n, d in result["distance"].items() if math.isfinite(d)}
    control = DirectedGraph()
    for node in graph.adj:
        if node in layers:
            control.add_node(node)
    for u, v, weight in graph.edges():
        if u in layers and v in layers and layers[u] < layers[v]:
            control.add_edge(u, v, weight)
    return control, layers


def nested_induced_graphs(graph, seed=42):
    """Amostra de vértices uniforme sem reposição, prefixos aninhados, arestas induzidas."""
    shuffled = sorted(graph.adj)
    random.Random(seed).shuffle(shuffled)
    samples = []
    for fraction in (0.1, 0.5, 1.0):
        size = max(1, round(len(shuffled) * fraction))
        chosen = set(shuffled[:size])
        sample = DirectedGraph()
        for node in sorted(chosen):
            sample.add_node(node)
        for source, target, weight in graph.edges():
            if source in chosen and target in chosen:
                sample.add_edge(source, target, weight)
        samples.append({"fraction": fraction, "graph": sample, "selected_nodes": sorted(chosen)})
    return samples


def summarize_times(samples):
    return {
        "repetitions": len(samples), "seconds": samples,
        "mean_seconds": statistics.mean(samples), "median_seconds": statistics.median(samples),
        "stdev_seconds": statistics.stdev(samples) if len(samples) > 1 else 0.0,
        "min_seconds": min(samples), "max_seconds": max(samples),
    }


def _negative_source(graph):
    """Escolhe o menor ID em ciclo recíproco negativo, quando existir."""
    weights = {(u, v): w for u, v, w in graph.edges()}
    candidates = sorted(u for (u, v), w in weights.items() if (v, u) in weights and w + weights[(v, u)] < 0)
    return candidates[0] if candidates else select_sources(graph)[0]


def _finite_count(result):
    return sum(math.isfinite(d) for d in result["distance"].values())


def _benchmark(graph, repetitions):
    measurements = []
    full_results = {}
    for sample in nested_induced_graphs(graph):
        subgraph = sample["graph"]
        transformed = transform_graph(subgraph)
        source = select_sources(subgraph)[0]
        negative_source = _negative_source(subgraph)
        for name, operation, model, start in (
            ("BFS", bfs, subgraph, source), ("DFS", dfs, subgraph, source),
            ("Dijkstra", dijkstra, transformed, source),
            ("Bellman-Ford", bellman_ford, subgraph, negative_source),
        ):
            times = []
            for _ in range(repetitions):
                before = time.perf_counter()
                result = operation(model, start)
                times.append(time.perf_counter() - before)
            row = {
                "algorithm": name, "fraction": sample["fraction"], "nodes": len(subgraph),
                "edges": sum(len(a) for a in subgraph.adj.values()), "source": start,
                "weight_model": "10-rating" if name == "Dijkstra" else "rating (ignorado por BFS/DFS)" if name in ("BFS", "DFS") else "rating",
                "task": "árvore de alcance" if name == "BFS" else "travessia/classificação" if name == "DFS" else "menores custos não negativos" if name == "Dijkstra" else "menores saldos e detecção/propagação de ciclo negativo",
                **summarize_times(times), "selected_nodes": sample["selected_nodes"],
            }
            measurements.append(row)
            print(f"[parte2] {name:12} {sample['fraction']:.0%}: n={len(subgraph)}, m={row['edges']}, mediana={row['median_seconds']:.6f}s", flush=True)
            if sample["fraction"] == 1.0:
                full_results[name] = (start, result)
    return measurements, full_results


def _metrics(graph, records):
    incoming = Counter(r.target for r in records)
    outgoing_negative = Counter(r.source for r in records if r.rating < 0)
    incoming_negative = Counter(r.target for r in records if r.rating < 0)
    incoming_sum = Counter()
    for r in records:
        incoming_sum[r.target] += r.rating
    rows = [{"node": n, "in_degree": incoming[n], "out_degree": len(graph.adj[n]),
             "negative_received": incoming_negative[n], "negative_sent": outgoing_negative[n],
             "mean_received_rating": incoming_sum[n] / incoming[n] if incoming[n] else None}
            for n in graph.adj]
    edge_pairs = {(r.source, r.target) for r in records}
    reciprocal = sum((v, u) in edge_pairs for u, v in edge_pairs)
    structure = {
        "density_without_loops": (len(edge_pairs) - sum(u == v for u, v in edge_pairs)) / (len(graph) * (len(graph) - 1)) if len(graph) > 1 else 0,
        "reciprocal_arcs": reciprocal, "reciprocal_arc_fraction": reciprocal / len(edge_pairs),
        "zero_in_degree": sum(row["in_degree"] == 0 for row in rows),
        "zero_out_degree": sum(row["out_degree"] == 0 for row in rows),
        "top_in_degree": sorted(rows, key=lambda r: (-r["in_degree"], r["node"]))[:10],
        "top_out_degree": sorted(rows, key=lambda r: (-r["out_degree"], r["node"]))[:10],
        "top_negative_received": sorted(rows, key=lambda r: (-r["negative_received"], r["node"]))[:10],
    }
    return rows, structure


def measure_required_cases(graph, costs, traversals, cases, bf_cases, repetitions, scaling_benchmarks):
    """Cinco medições por caso obrigatório, além das medições de escalabilidade.

    Dijkstra executa a busca completa da fonte e reconstrói o destino em cada
    repetição. O caso cíclico reutiliza exatamente a tarefa já medida na rede
    completa, explicitamente identificado para não simular amostras adicionais.
    """
    measurements = []
    def measure(name, source, target, operation, model):
        durations = []
        for _ in range(repetitions):
            before = time.perf_counter()
            operation()
            durations.append(time.perf_counter() - before)
        measurements.append({"algorithm": name, "source": source, "target": target,
                             "case": model, "measurement_origin": "new_case_measurement",
                             **summarize_times(durations)})
    for traversal in traversals:
        source = traversal["source"]
        measure("BFS", source, None, lambda s=source: bfs(graph, s), "alcance original por fonte")
        measure("DFS", source, None, lambda s=source: dfs(graph, s), "travessia/classificação original por fonte")
    for case in cases:
        source, target = case["source"], case["target"]
        def shortest_case(s=source, t=target):
            result = dijkstra(costs, s)
            return reconstruct_path(result["parent"], s, t)
        measure("Dijkstra", source, target, shortest_case, "10-rating; busca completa da fonte e reconstrução do par")
    dag_case = bf_cases["acyclic_control"]
    control, _ = increasing_layer_dag(graph, dag_case["source"])
    measure("Bellman-Ford", dag_case["source"], dag_case["target"],
            lambda: bellman_ford(control, dag_case["source"]), "controle DAG com ratings negativos reais")
    cyclic = bf_cases["original_negative_cycle"]
    measured = next(row for row in scaling_benchmarks if row["algorithm"] == "Bellman-Ford" and row["fraction"] == 1.0)
    if measured["source"] != cyclic["source"]:
        raise ValueError("Medições reaproveitadas devem corresponder à mesma fonte/tarefa cíclica.")
    measurements.append({"algorithm": "Bellman-Ford", "source": cyclic["source"], "target": None,
                         "case": "rede original; detecção/propagação de ciclo negativo",
                         "measurement_origin": "reused_scaling_full_graph_not_new_samples",
                         **summarize_times(list(measured["seconds"]))})
    return measurements


def _write_case_csv(out, case_benchmarks):
    rows = []
    for case in case_benchmarks:
        for index, seconds in enumerate(case["seconds"], start=1):
            rows.append({"algorithm": case["algorithm"], "source": case["source"], "target": case["target"],
                         "case": case["case"], "measurement_origin": case["measurement_origin"],
                         "repetition": index, "seconds": seconds,
                         "mean_seconds": case["mean_seconds"], "median_seconds": case["median_seconds"]})
    _write_csv(Path(out) / "case_benchmarks.csv", rows)


def _clean_json(value):
    if isinstance(value, float) and not math.isfinite(value):
        return "-inf" if value < 0 else "inf"
    if isinstance(value, dict):
        return {str(k): _clean_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean_json(v) for v in value]
    if isinstance(value, set):
        return [_clean_json(v) for v in sorted(value)]
    return value


def _write_csv(path, rows, fieldnames=None):
    if not rows:
        return
    with Path(path).open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _traverse(graph, sources):
    traversals = []
    for source in sources:
        breadth = bfs(graph, source)
        depth = dfs(graph, source)
        layers = {n: d for n, d in breadth["distance"].items() if math.isfinite(d)}
        traversals.append({
            "source": source, "reachable": len(layers), "unreachable": len(graph) - len(layers),
            "max_distance": max(layers.values()),
            "bfs": {"order": breadth["order"], "parent": breadth["parent"], "layers": layers,
                    "layer_counts": dict(sorted(Counter(layers.values()).items()))},
            "dfs": {"order": depth["order"], "parent": depth["parent"], "discover": depth["discover"],
                    "finish": depth["finish"], "has_cycle": depth["has_cycle"],
                    "classification_counts": dict(Counter(item[2] for item in depth["classification"])),
                    "classification": depth["classification"]},
        })
    return traversals


def _pair_cases(graph, costs, traversals):
    cases = []
    for traversal in traversals:
        source = traversal["source"]
        candidates = sorted((n for n in traversal["bfs"]["layers"] if n != source),
                            key=lambda n: (traversal["bfs"]["layers"][n], n))
        selected = []
        for fraction in (0.25, 0.65, 1.0):
            if candidates:
                node = candidates[min(len(candidates) - 1, max(0, round((len(candidates) - 1) * fraction)))]
                if node not in selected:
                    selected.append(node)
        result = dijkstra(costs, source)
        for target in selected:
            path = reconstruct_path(result["parent"], source, target)
            breadth_path = reconstruct_path(traversal["bfs"]["parent"], source, target)
            cases.append({
                "source": source, "target": target, "reachable": True,
                "dijkstra_path": path, "dijkstra_steps": len(path) - 1,
                "dijkstra_cost_10_minus_rating": result["distance"][target],
                "dijkstra_path_original_rating_sum": path_weight(graph, path),
                "bfs_path": breadth_path, "bfs_steps": len(breadth_path) - 1,
                "bfs_path_cost_10_minus_rating": path_weight(costs, breadth_path),
                "bfs_path_original_rating_sum": path_weight(graph, breadth_path),
            })
    return cases


def _bf_cases(graph, traversal, full_result):
    source = traversal["source"]
    dag, layers = increasing_layer_dag(graph, source)
    result = bellman_ford(dag, source)
    finite = {n: d for n, d in result["distance"].items() if math.isfinite(d)}
    target = min((n for n in finite if n != source), key=lambda n: (finite[n], n))
    path = reconstruct_path(result["parent"], source, target)
    cycle_source, cyclic = full_result
    cycle = cyclic["negative_cycle"]
    cycle_cost = path_weight(graph, cycle) if cycle else None
    if not cycle or cycle[0] != cycle[-1] or cycle_cost >= 0:
        raise RuntimeError("O caso da rede original deve exibir um ciclo negativo real fechado.")
    return {
        "acyclic_control": {
            "source": source, "nodes": len(dag), "edges": sum(len(a) for a in dag.adj.values()),
            "negative_edges": sum(w < 0 for _, _, w in dag.edges()),
            "rule": "arco u->v preservado somente se camada_BFS(u)<camada_BFS(v); vértices alcançáveis; pesos/direções originais",
            "removed_edges": sum(len(a) for a in graph.adj.values()) - sum(len(a) for a in dag.adj.values()),
            "acyclic_proof": "A camada inteira aumenta em cada arco; portanto nenhum ciclo pode fechar.",
            "negative_cycle": result["negative_cycle"], "affected": sorted(result["affected"]),
            "target": target, "path": path, "cost": finite[target], "steps": len(path) - 1,
            "distances": result["distance"], "parents": result["parent"], "layers": layers,
            "scope_note": "Controle experimental com arestas removidas. Não implica que a rede original seja acíclica nem resolve os mínimos dela.",
        },
        "original_negative_cycle": {
            "source": cycle_source, "negative_cycle": cycle, "cycle_cost": cycle_cost,
            "cycle_edges": [{"source": u, "target": v, "weight": path_weight(graph, [u, v])} for u, v in zip(cycle, cycle[1:])],
            "affected_count": len(cyclic["affected"]), "affected": sorted(cyclic["affected"]),
            "finite_count": _finite_count(cyclic),
            "unreachable_count": sum(d == math.inf for d in cyclic["distance"].values()),
            "distances": cyclic["distance"],
            "interpretation": "Para vértices alcançáveis após o ciclo, repetir o ciclo reduz indefinidamente a soma de ratings: não existe mínimo finito. Não é lucro nem dívida monetária.",
        },
    }


def _render(payload, records, node_rows, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    import numpy as np

    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": "white", "savefig.facecolor": "white", "axes.titleweight": "bold"})
    figures = []
    def save(fig, name, caption):
        fig.savefig(out / f"{name}.png", dpi=170, bbox_inches="tight")
        plt.close(fig)
        figures.append({"file": f"{name}.png", "caption": caption})
    colors = {"negative": "#bd3b39", "zero": "#8c939d", "positive": "#247d7c"}

    fig, ax = plt.subplots(figsize=(10, 5))
    counts = Counter(r.rating for r in records)
    x = list(range(-10, 11))
    ax.bar(x, [counts[n] for n in x], color=[colors["negative" if n < 0 else "positive" if n > 0 else "zero"] for n in x])
    ax.set(xticks=x, xlabel="Rating recebido no registro (escala original)", ylabel="Número de avaliações", title="Distribuição dos ratings por sinal na versão analisada")
    sign_labels = {"negative": "Negativo", "zero": "Zero", "positive": "Positivo"}
    ax.text(.02, .95, " · ".join(f"{sign_labels[key]}: {payload['dataset']['sign_counts'][key]:,}" for key in ("negative", "zero", "positive")), transform=ax.transAxes, va="top")
    ax.legend(handles=[Patch(facecolor=colors[key], label=sign_labels[key]) for key in sign_labels], title="Sinal do rating")
    save(fig, "exploratoria_01_ratings", "Distribuição de todos os ratings do CSV recebido, incluindo frequências zero na escala. Cores indicam sinal, não probabilidade de confiança.")

    fig, ax = plt.subplots(figsize=(9, 6))
    scatter = ax.scatter([r["out_degree"] for r in node_rows], [r["in_degree"] for r in node_rows],
                         c=[r["negative_received"] for r in node_rows], cmap="magma_r", s=16, alpha=.65, linewidth=0)
    ax.set_xscale("symlog", linthresh=1); ax.set_yscale("symlog", linthresh=1)
    ax.set(xlabel="Grau de saída: avaliações emitidas (symlog)", ylabel="Grau de entrada: avaliações recebidas (symlog)", title="Concentração de atividade e avaliações negativas por usuário")
    for row in payload["structure"]["top_in_degree"][:3]:
        ax.annotate(str(row["node"]), (row["out_degree"], row["in_degree"]), xytext=(5, 5), textcoords="offset points")
    fig.colorbar(scatter, ax=ax, label="Número de avaliações negativas recebidas")
    save(fig, "exploratoria_02_graus", "Cada ponto é um usuário. Escala symlog mantém zeros. Rótulos identificam os três maiores graus de entrada; sobreposição pode esconder pontos.")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [1, 1.4]})
    sources = [str(t["source"]) for t in payload["traversals"]]
    axes[0].bar(sources, [t["reachable"] for t in payload["traversals"]], label="Alcançáveis", color="#247d7c")
    axes[0].bar(sources, [t["unreachable"] for t in payload["traversals"]], bottom=[t["reachable"] for t in payload["traversals"]], label="Inalcançáveis", color="#d7dade")
    axes[0].set(xlabel="Usuário fonte", ylabel="Número de usuários", title="Alcance depende da direção"); axes[0].legend()
    for item in payload["traversals"]:
        counts_layer = item["bfs"]["layer_counts"]
        axes[1].plot(list(counts_layer), list(counts_layer.values()), "o-", label=f"Fonte {item['source']}")
    axes[1].set(xlabel="Distância BFS (número mínimo de arcos)", ylabel="Usuários na camada", title=f"Camadas de {len(payload['traversals'])} fontes determinísticas"); axes[1].legend()
    save(fig, "exploratoria_03_alcance", "BFS ignora rating. A fonte conta na camada zero. Ausência de caminho dirigido não implica ausência de relação social fora dos registros.")

    months = sorted({datetime.fromtimestamp(r.timestamp, timezone.utc).strftime("%Y-%m") for r in records})
    monthly = {sign: Counter() for sign in colors}
    for r in records:
        sign = "negative" if r.rating < 0 else "positive" if r.rating > 0 else "zero"
        monthly[sign][datetime.fromtimestamp(r.timestamp, timezone.utc).strftime("%Y-%m")] += 1
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.stackplot(range(len(months)), *[[monthly[s][m] for m in months] for s in ("positive", "zero", "negative")],
                 labels=["Positivo", "Zero", "Negativo"], colors=[colors[s] for s in ("positive", "zero", "negative")])
    ticks = list(range(0, len(months), max(1, len(months) // 10)))
    ax.set(xticks=ticks, xticklabels=[months[n] for n in ticks], xlabel="Mês de registro (UTC)", ylabel="Número de avaliações", title="Volume e sinais variam ao longo dos meses registrados")
    ax.tick_params(axis="x", rotation=35); ax.legend(loc="upper left")
    save(fig, "exploratoria_04_tempo", "Agregação mensal UTC dos registros disponíveis. Não estima usuários ativos, causalidade ou evolução de confiança individual.")

    cases = payload["dijkstra_cases"]
    labels = [f"{c['source']}→{c['target']}" for c in cases]
    positions = np.arange(len(cases))
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    for ax, a, b, ylabel in (
        (axes[0], "bfs_steps", "dijkstra_steps", "Número de arcos"),
        (axes[1], "bfs_path_cost_10_minus_rating", "dijkstra_cost_10_minus_rating", "Custo ∑(10 − rating)"),
    ):
        ax.bar(positions - .18, [c[a] for c in cases], .36, label="Caminho BFS", color="#8d9bb0")
        ax.bar(positions + .18, [c[b] for c in cases], .36, label="Caminho Dijkstra", color="#247d7c")
        ax.set_ylabel(ylabel); ax.legend()
    axes[0].set_title("Dijkstra minimiza o custo transformado; pode usar mais arcos")
    axes[1].set(xticks=positions, xticklabels=labels, xlabel="Par dirigido fonte → destino (alcançável)")
    save(fig, "explanatoria_01_objetivos", "Comparação nos mesmos pares. BFS minimiza arcos; Dijkstra minimiza ∑(10-rating). O termo 10 é cobrado a cada arco: não equivale a maximizar a soma de ratings quando o número de arcos varia.")

    cyc = payload["bellman_ford_cases"]["original_negative_cycle"]
    control = payload["bellman_ford_cases"]["acyclic_control"]
    cycle_nodes = cyc["negative_cycle"][:-1]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    angles = np.linspace(0, 2 * math.pi, len(cycle_nodes), endpoint=False) + math.pi / 2
    coords = {node: (math.cos(a), math.sin(a)) for node, a in zip(cycle_nodes, angles)}
    ax = axes[0]
    for node, (x, y) in coords.items():
        ax.scatter([x], [y], s=1100, c="#edf4f3", edgecolor="#247d7c", zorder=3)
        ax.text(x, y, str(node), ha="center", va="center", zorder=4)
    for edge in cyc["cycle_edges"]:
        a, b = coords[edge["source"]], coords[edge["target"]]
        ax.annotate("", xy=b, xytext=a, arrowprops={"arrowstyle": "-|>", "color": "#bd3b39", "lw": 2, "shrinkA": 20, "shrinkB": 20, "connectionstyle": "arc3,rad=0.24"})
        dx, dy = b[0] - a[0], b[1] - a[1]
        ax.text((a[0] + b[0]) / 2 + dy * .15, (a[1] + b[1]) / 2 - dx * .15, str(edge["weight"]), ha="center", bbox={"facecolor": "white", "edgecolor": "none"})
    ax.set(xlim=(-1.6, 1.6), ylim=(-1.4, 1.5), title=f"Ciclo real: soma {cyc['cycle_cost']}"); ax.axis("off")
    ax.legend(handles=[Line2D([], [], marker="o", linestyle="none", markerfacecolor="#edf4f3", markeredgecolor="#247d7c", label="Usuário"),
                       Line2D([], [], color="#bd3b39", marker=">", label="Arco do ciclo (peso indicado)")], loc="lower center", fontsize=8)
    axes[1].axis("off")
    axes[1].text(0, .95, f"Rede original, fonte {cyc['source']}\n\n{cyc['affected_count']:,} usuários sem mínimo finito\n{cyc['finite_count']:,} com mínimo finito\n{cyc['unreachable_count']:,} inalcançáveis\n\nControle acíclico, fonte {control['source']}\n\n{control['nodes']:,} nós · {control['edges']:,} arcos\n{control['negative_edges']:,} arcos negativos preservados\nMenor saldo observado: {control['cost']}\nDestino {control['target']} em {control['steps']} arcos", va="top", fontsize=12)
    fig.suptitle("Bellman-Ford separa saldo finito de repetição negativa ilimitada", weight="bold")
    save(fig, "explanatoria_02_ciclo", "O ciclo foi validado arco a arco no CSV recebido. O controle retira arcos que não avançam nas camadas BFS; não descreve a rede original como acíclica.")

    full = [b for b in payload["benchmarks"] if b["fraction"] == 1.0]
    fig, ax = plt.subplots(figsize=(9, 5))
    algorithm_colors = ["#8d9bb0", "#64748b", "#247d7c", "#bd3b39"]
    ax.bar([b["algorithm"] for b in full], [b["median_seconds"] for b in full], color=algorithm_colors)
    ax.legend(handles=[Patch(facecolor=color, label=b["algorithm"]) for b, color in zip(full, algorithm_colors)], loc="upper left", title="Algoritmo/tarefa")
    ax.set_yscale("log")
    ax.set(ylabel="Mediana de tempo (s, escala log)", xlabel="Algoritmo e tarefa documentada", title=f"Rede completa: {payload['repetitions']} execuções medidas por tarefa")
    for idx, row in enumerate(full):
        ax.text(idx, row["median_seconds"] * 1.15, f"{row['median_seconds']:.4g} s", ha="center")
    save(fig, "comparacao_algoritmos", "Tempos do mesmo ambiente, excluindo leitura/construção/figuras. Tarefas e pesos diferem: BFS/DFS alcance, Dijkstra custo transformado, BF saldo original e ciclos; não é ranking de algoritmos equivalentes.")

    fig, ax = plt.subplots(figsize=(10, 5))
    for name, color in (("BFS", "#8d9bb0"), ("DFS", "#64748b"), ("Dijkstra", "#247d7c"), ("Bellman-Ford", "#bd3b39")):
        data = [b for b in payload["benchmarks"] if b["algorithm"] == name]
        medians = [b["median_seconds"] for b in data]
        ax.errorbar([100 * b["fraction"] for b in data], medians,
                    yerr=[[b["median_seconds"] - b["min_seconds"] for b in data], [b["max_seconds"] - b["median_seconds"] for b in data]],
                    fmt="o-", capsize=3, label=name, color=color)
    ax.set_yscale("log")
    ax.set(xticks=[10, 50, 100], xlabel="Nós selecionados (%, subgrafos induzidos aninhados; seed 42)", ylabel="Tempo (s, escala log)", title="Escala medida: mediana e intervalo mínimo–máximo")
    ax.legend()
    save(fig, "benchmark_tempos", "Amostra uniforme de nós, mantendo inclusive isolados e todas as arestas induzidas. Contagens reais e tempos individuais estão no JSON/CSV. Três tamanhos não provam complexidade assintótica.")
    return figures


def _analysis(payload):
    dataset = payload["dataset"]
    structure = payload["structure"]
    cyc = payload["bellman_ford_cases"]["original_negative_cycle"]
    dag = payload["bellman_ford_cases"]["acyclic_control"]
    cases = payload["dijkstra_cases"]
    changed = sum(c["bfs_path"] != c["dijkstra_path"] for c in cases)
    more = sum(c["dijkstra_steps"] > c["bfs_steps"] for c in cases)
    positive_fraction = dataset["sign_counts"]["positive"] / dataset["rows"]
    top = structure["top_in_degree"][0]
    top_negative = structure["top_negative_received"][0]
    findings = [
        f"O arquivo preservado contém {dataset['rows']} avaliações dirigidas e {dataset['nodes']} usuários; SHA-256 {dataset['sha256']}.",
        f"Há {dataset['sign_counts']['positive']} avaliações positivas ({positive_fraction:.2%}), {dataset['sign_counts']['negative']} negativas e {dataset['sign_counts']['zero']} zeros. Média {dataset['rating_mean']:.3f}; mediana {dataset['rating_median']}.",
        f"A densidade dirigida sem laços é {structure['density_without_loops']:.6f}. {structure['reciprocal_arc_fraction']:.2%} dos arcos têm o arco reverso; isto não indica concordância de ratings.",
        f"O usuário {top['node']} recebe {top['in_degree']} avaliações, maior grau de entrada observado. Há {structure['zero_in_degree']} usuários sem entrada e {structure['zero_out_degree']} sem saída.",
        f"O usuário {top_negative['node']} recebe {top_negative['negative_received']} avaliações negativas entre {top_negative['in_degree']} recebidas, com média {top_negative['mean_received_rating']:.3f}; é o maior número absoluto de negativas recebidas, não uma prova sobre sua identidade ou conduta.",
        "Alcance BFS por fonte: " + "; ".join(f"{t['source']}: {t['reachable']} alcançáveis, {t['unreachable']} inalcançáveis, profundidade máxima {t['max_distance']}" for t in payload["traversals"]) + ".",
        f"Nos {len(cases)} pares alcançáveis, Dijkstra escolheu caminho diferente de BFS em {changed}; usou mais arcos em {more}. Em todos, o custo transformado de Dijkstra é menor ou igual ao do caminho BFS.",
        f"O controle em DAG conserva {dag['nodes']} nós/{dag['edges']} arcos, incluindo {dag['negative_edges']} negativos. Da fonte {dag['source']}, o menor saldo finito é {dag['cost']} até {dag['target']}.",
        f"Na rede original, BF da fonte {cyc['source']} encontra ciclo {cyc['negative_cycle']} de soma {cyc['cycle_cost']}; {cyc['affected_count']} vértices não têm mínimo finito. Repetir o ciclo permite somas arbitrariamente negativas.",
        f"Ausências: {dataset['missing_by_column']}; pares dirigidos repetidos: {dataset['duplicate_directed_pairs']}; laços: {dataset['self_loops']}. Zero ausências observadas não determina mecanismo de ausência nem completude social.",
    ]
    lines = ["# Parte 2 — alcance, sinais e saldo de avaliações", "", "## Pergunta e modelos", "",
             "Como o alcance dirigido varia entre fontes, como se distribuem os sinais e quando existe um saldo mínimo finito de avaliações?", "",
             "BFS/DFS ignoram os ratings e investigam alcance/estrutura. Bellman-Ford minimiza a soma dos ratings originais: procurar valores menores acumula desconfiança e não mede confiança transitiva. Dijkstra usa 10-rating em cada arco, com custos de 0 a 20; isto penaliza avaliações menores e cobra 10 por arco. Os objetivos são diferentes e não são comparados como se fossem equivalentes.", "",
             "## Evidências medidas", ""]
    lines += [f"- {finding}" for finding in findings]
    lines += ["", "## Desenho experimental", "",
              f"As {len(payload['traversals'])} fontes são escolhidas de forma determinística: maior grau de saída; maior número de avaliações negativas emitidas; e posição mediana entre usuários com saída. Empates usam ID e duplicações são substituídas pelo próximo maior grau. Para cada fonte, escolhem-se destinos nas posições 25%, 65% e 100% da ordenação (distância BFS, ID), sem repetir destinos.", "",
              "O controle de Bellman-Ford mantém apenas vértices alcançáveis e arcos reais que avançam estritamente nas camadas BFS. Os pesos e direções permanecem originais; o aumento estrito da camada prova ausência de ciclos. Este controle altera a rede e não autoriza conclusões de aciclicidade sobre a rede original.", "",
              f"Benchmarks: {payload['repetitions']} execuções por algoritmo/tarefa em 10%, 50% e 100% dos nós. Embaralhamento dos IDs ordenados com random.Random(42); prefixos aninhados e todas as arestas induzidas, incluindo nós isolados. A fonte de BFS/DFS/Dijkstra é a de maior saída em cada subgrafo. BF prefere o menor ID participante de ciclo recíproco negativo; se não existir, usa maior saída. As fontes constam no CSV. O tempo usa perf_counter, inclui criação do resultado e detecção/propagação dos ciclos, e exclui leitura, construção dos modelos e renderização. Não há remoção de outliers temporais, aquecimento descartado ou timeout escondido.", "",
              "| Nós selecionados | Nós reais | Arcos reais | Algoritmo | Fonte | Média (s) | Mediana (s) | Mínimo–máximo (s) |", "|---|---:|---:|---|---:|---:|---:|---:|"]
    for b in payload["benchmarks"]:
        lines.append(f"| {b['fraction']:.0%} | {b['nodes']} | {b['edges']} | {b['algorithm']} | {b['source']} | {b['mean_seconds']:.7f} | {b['median_seconds']:.7f} | {b['min_seconds']:.7f}–{b['max_seconds']:.7f} |")
    lines += ["", f"## {payload['repetitions']} medições por caso obrigatório", "",
              f"Além da escala, BFS/DFS são medidos separadamente por fonte; Dijkstra por par, incluindo a busca completa da fonte e reconstrução do destino; BF no controle DAG. O caso BF original reutiliza as {payload['repetitions']} medições da mesma fonte e tarefa em 100%, sem contá-las como novas amostras. Séries individuais e origem estão em case_benchmarks.csv e no JSON.", "",
              "| Algoritmo | Fonte | Destino | Caso | Média (s) | Mediana (s) |", "|---|---:|---:|---|---:|---:|"]
    for b in payload.get("case_benchmarks", []):
        lines.append(f"| {b['algorithm']} | {b['source']} | {b['target'] if b['target'] is not None else '—'} | {b['case']} | {b['mean_seconds']:.7f} | {b['median_seconds']:.7f} |")
    lines += ["", "## Comparação de ordens e estrutura", "",
              "BFS organiza vértices por distância mínima em arcos; DFS aprofunda cada ramo antes de retornar. A ordem depende da ordem dos arcos do arquivo preservado e não constitui um ranking dos usuários. Ambos alcançam o mesmo conjunto por fonte. Arcos de retorno na DFS testemunham ciclos dirigidos, mas não determinam o sinal total de um ciclo.", ""]
    for traversal in payload["traversals"]:
        lines += [f"- Fonte {traversal['source']}: primeiros 12 em BFS: {traversal['bfs']['order'][:12]}; em DFS: {traversal['dfs']['order'][:12]}. Classificações DFS: {traversal['dfs']['classification_counts']}; ciclo alcançável: {traversal['dfs']['has_cycle']}."]
    lines += ["", "## Ambiente e limites", "", f"Python {payload['environment']['python']}; {payload['environment']['platform']}; processador {payload['environment']['processor'] or 'não informado pelo sistema'}. Medição local, sem controle de carga de fundo. Tempos não são previsão de desempenho em outra máquina e três tamanhos não demonstram limites assintóticos.", "",
              dataset["version_note"] + " O experimento usa somente os bytes do arquivo selecionado. A rede deve ser interpretada no contexto da versão e da plataforma documentadas. Concentração, correlação, ausência de caminho e distribuição de sinais não estabelecem causalidade, identidade, recomendação de confiança, nem representatividade de outras plataformas. Não há inferência de mecanismo de dados ausentes a partir de zero campos vazios.", "",
              "Toda implementação, seleção operacional dos casos, análise e figuras desta entrega receberam assistência integral de IA. Autoria e contribuições humanas não são simuladas.", "", "## Figuras", ""]
    lines += [f"- [{fig['file']}]({fig['file']}): {fig['caption']}" for fig in payload["figures"]]
    lines += ["", "## Referência", "", "Stanford SNAP, Bitcoin Alpha: https://snap.stanford.edu/data/soc-sign-bitcoin-alpha.html. Kumar et al., Edge Weight Prediction in Weighted Signed Networks, IEEE ICDM, 2016.", ""]
    return findings, "\n".join(lines)


def figure_notes(payload):
    """Notas interpretativas vinculadas aos resultados, sem inferir mecanismos sociais."""
    d, s = payload["dataset"], payload["structure"]
    c = payload["bellman_ford_cases"]["original_negative_cycle"]
    dag = payload["bellman_ford_cases"]["acyclic_control"]
    largest = s["top_negative_received"][0]
    top_in = s["top_in_degree"][0]
    full_bf = next(b for b in payload["benchmarks"] if b["algorithm"] == "Bellman-Ford" and b["fraction"] == 1)
    reach_summary = "; ".join(f"fonte {t['source']}: {t['reachable']} alcançáveis, {t['unreachable']} inalcançáveis, profundidade máxima {t['max_distance']}" for t in payload["traversals"])
    scale_summary = "; ".join(f"{b['fraction']:.0%}: {b['nodes']}/{b['edges']}" for b in payload["benchmarks"] if b["algorithm"] == "BFS")
    cases = payload["dijkstra_cases"]
    more_arcs = sum(case["dijkstra_steps"] > case["bfs_steps"] for case in cases)
    lower_cost = sum(case["dijkstra_cost_10_minus_rating"] < case["bfs_path_cost_10_minus_rating"] for case in cases)
    equal_cost = sum(case["dijkstra_cost_10_minus_rating"] == case["bfs_path_cost_10_minus_rating"] for case in cases)
    missing_total = sum(d["missing_by_column"].values())
    notes = [
        "# Notas analíticas das figuras — Parte 2 [IA]", "",
        "Autoria assistida integralmente por IA. Estas notas explicam os resultados medidos, o desenho dos gráficos e seus limites.", "",
        "## Variáveis e papéis", "",
        "SOURCE e TARGET são identificadores nominais: o valor numérico do ID não mede importância, confiança ou ordem temporal. SOURCE é emissor da avaliação e TARGET é receptor. Graus de saída/entrada são contagens nesses papéis. RATING é uma escala discreta assinada definida pela plataforma; as somas e médias são uma convenção operacional deste experimento e não unidades psicológicas de confiança. TIME é temporal (segundos Unix); os meses são UTC. Os gráficos relacionam rating com mês e com contagens de emissão/recepção, preservando os papéis dirigidos.", "",
        "## 1. Exploratória — distribuição dos ratings", "",
        f"Mostra a contagem em cada valor de -10 a 10, inclusive valores sem registros. Há {d['sign_counts']['positive']} avaliações positivas ({d['sign_counts']['positive']/d['rows']:.2%}), {d['sign_counts']['negative']} negativas e {d['sign_counts']['zero']} zeros. Barras são adequadas à escala discreta e deixam frequências nulas visíveis. As três cores e a legenda identificam o sinal, e o eixo cobre a escala completa. A frequência dos sinais não autoriza concluir que a rede inteira é confiável.", "",
        "## 2. Exploratória — relação entre emissão, recepção e negativas", "",
        f"Cada ponto combina grau de saída (emissor), grau de entrada (receptor) e cor para o número de negativas recebidas: três variáveis derivadas dos registros. O usuário {top_in['node']} tem maior entrada ({top_in['in_degree']}); {largest['node']} recebe {largest['negative_received']} negativas em {largest['in_degree']} avaliações. Dispersão permite procurar concentração, associação e casos fora da tendência; symlog acomoda zeros e uma faixa ampla. Os rótulos destacam maiores entradas, não IDs numericamente maiores. A barra de cores explicita as contagens de negativas. A cor é contagem absoluta, portanto também depende da exposição; não é taxa de risco e a relação não prova causalidade. Pontos sobrepostos podem ocultar usuários.", "",
        "## 3. Exploratória — alcance e distância dirigida", "",
        f"As barras separam alcançáveis de inalcançáveis, e as linhas mostram quantos usuários surgem em cada camada. Resultados desta versão: {reach_summary}. Barras com parte/todo e linhas em distâncias inteiras facilitam comparar volume e distribuição. As legendas distinguem os conjuntos e as fontes. Destaques são os vértices inalcançáveis e as camadas mais distantes de cada fonte, com contagens descritas acima. BFS ignora rating, e ausência de caminho não prova ausência de relação fora do arquivo.", "",
        "## 4. Exploratória — rating e tempo de registro", "",
        f"A área empilhada separa volumes mensais positivos, negativos e zeros, expondo variação temporal de contagens e sinais. O pico total ocorre em {d['monthly_peak_utc']['month']} com {d['monthly_peak_utc']['count']} registros. A área evidencia composição e volume; meses ordenados permitem localizar o pico, sem usar ID como tempo. O destaque não identifica a causa, não conta usuários ativos e não acompanha a mudança de opinião de uma mesma pessoa. A categoria zero permanece identificada na legenda e tem {d['sign_counts']['zero']} registros nesta versão.", "",
        "## Da exploração à explicação", "",
        "As explorações investigam a distribuição de sinais, a concentração de avaliações e o alcance dirigido da versão selecionada. As explicações seguintes isolam duas consequências verificáveis: transformar ratings muda o objetivo dos caminhos; conservar ciclos negativos pode eliminar o mínimo finito. Não se escolheu um caminho para recomendar confiança nem para movimentar bitcoins.", "",
        "## 5. Explanatória — dois objetivos nos mesmos pares", "",
        f"Duas barras por par comparam BFS e Dijkstra em número de arcos e em soma de 10-rating, em painéis com as mesmas categorias. Dijkstra usa mais arcos em {more_arcs} dos {len(cases)} pares; obtém custo transformado estritamente menor em {lower_cost} e igual em {equal_cost}. Barras agrupadas facilitam comparação par a par; os dois painéis mostram a relação observada entre número de arcos e custo. O destaque é que minimizar quantidade de arcos e custo transformado são objetivos distintos, mesmo quando os resultados coincidem. Como ∑(10-rating)=10k−∑rating, variar k impede tratar a transformação como equivalente ao mínimo original ou a confiança transitiva.", "",
        "## 6. Explanatória — ciclo negativo e controle finito", "",
        f"O diagrama mostra o ciclo real {' → '.join(map(str,c['negative_cycle']))}, com soma {c['cycle_cost']}, e o painel contrasta seus {c['affected_count']} usuários afetados com o controle DAG de {dag['nodes']} nós/{dag['edges']} arcos, que preserva {dag['negative_edges']} avaliações negativas. Um desenho local com setas, legenda e pesos permite conferir a direção e a soma sem esconder o ciclo no desenho da rede inteira; o texto distingue finito, inalcançável e sem mínimo. Repetir a soma negativa {c['cycle_cost']} reduz a soma ilimitadamente. O controle remove retornos entre camadas e não implica que a rede original seja acíclica; não há interpretação financeira.", "",
        "## 7. Comparação dos algoritmos — tempo na rede completa", "",
        f"As barras mostram medianas das {payload['repetitions']} execuções locais de cada tarefa. BF tem mediana {full_bf['median_seconds']:.6f}s, pois precisa detectar/propagar ciclos no modelo original; BFS/DFS/Dijkstra realizam tarefas distintas. A escala log permite visualizar ordens de grandeza sem ocultar tempos pequenos, os rótulos mostram segundos e a legenda identifica cada algoritmo/tarefa. O destaque é o custo medido do caso cíclico, não uma classificação universal de algoritmos. Médias, dispersão, fontes e tarefas constam das tabelas, impedindo confundir objetivos diferentes.", "",
        "## 8. Escalabilidade — três subgrafos induzidos", "",
        f"As linhas usam medianas e barras de mínimo–máximo dos subgrafos induzidos com seed 42. Contagens reais por fração de nós (nós/arcos): {scale_summary}. A fração de nós não fixa a fração de arcos, por isso ambas as contagens são informadas. Linhas evidenciam a mudança medida, e barras mostram a variação sem pressupor distribuição dos tempos. A escala log mantém as curvas legíveis, e a legenda identifica os algoritmos. Fontes e tarefas são documentadas; estes tamanhos, {payload['repetitions']} repetições e carga de fundo não demonstram uma lei assintótica nem desempenho em outra máquina.", "",
        "## Ausências, outliers e integridade", "",
        f"Foram observadas {missing_total} células ausentes nos campos exigidos; há {d['duplicate_directed_pairs']} pares repetidos e {d['self_loops']} laços. Zero campos ausentes não identifica o mecanismo de ausência, nem prova completude da rede. Outliers de grau e negativas são observações descritivas; não são erros descartados. {d['version_note']} Nenhuma execução temporal foi removida como outlier.", "",
    ]
    return "\n".join(notes)


def run_part2(root, out, repetitions=5, render=True, dataset=None):
    """Executa tudo a partir do CSV recebido; retorna e exporta o relatório estruturado."""
    if repetitions < 5:
        raise ValueError("São necessárias pelo menos 5 execuções por algoritmo/tarefa.")
    root, out = Path(root), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    dataset_file = Path(dataset) if dataset is not None else root / "data" / "dataset_parte2" / "bitcoinalpha.csv"
    records, metadata = read_ratings(dataset_file)
    try:
        metadata["file"] = dataset_file.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        metadata["file"] = dataset_file.name
    original = build_rating_graph(records)
    costs = transform_graph(original)
    node_rows, structure = _metrics(original, records)
    traversals = _traverse(original, select_sources(original))
    pair_cases = _pair_cases(original, costs, traversals)
    if len(pair_cases) < 5:
        raise ValueError("Dataset deve permitir pelo menos cinco pares alcançáveis distintos.")
    benchmarks, full_results = _benchmark(original, repetitions)
    payload = {
        "schema_version": 1, "dataset": metadata, "repetitions": repetitions,
        "environment": {"python": sys.version.split()[0], "implementation": platform.python_implementation(),
                        "platform": platform.platform(), "machine": platform.machine(), "processor": platform.processor(),
                        "timer": "time.perf_counter", "timestamp_utc": datetime.now(timezone.utc).isoformat()},
        "models": {"original": "arcos dirigidos SOURCE→TARGET, peso RATING; soma mínima de avaliações, não confiança transitiva",
                   "dijkstra": "custo por arco 10-RATING; não negativo; objetivo diferente do original",
                   "bfs_dfs": "direção original, pesos ignorados", "benchmark_sampling": "prefixos aninhados de IDs embaralhados com random.Random(42); subgrafos induzidos"},
        "structure": structure, "traversals": traversals, "dijkstra_cases": pair_cases,
        "bellman_ford_cases": _bf_cases(original, traversals[0], full_results["Bellman-Ford"]),
        "benchmarks": benchmarks, "figures": [],
    }
    payload["case_benchmarks"] = measure_required_cases(original, costs, traversals, pair_cases, payload["bellman_ford_cases"], repetitions, benchmarks)
    if render:
        payload["figures"] = _render(payload, records, node_rows, out)
    payload["findings"], analysis = _analysis(payload)
    (out / "analise.md").write_text(analysis, encoding="utf-8")
    (out / "notas_analiticas.md").write_text(figure_notes(payload), encoding="utf-8")
    _write_case_csv(out, payload["case_benchmarks"])
    _write_csv(out / "node_metrics.csv", node_rows)
    individual = []
    for row in benchmarks:
        for index, seconds in enumerate(row["seconds"], start=1):
            individual.append({"algorithm": row["algorithm"], "fraction": row["fraction"], "nodes": row["nodes"],
                               "edges": row["edges"], "source": row["source"], "repetition": index,
                               "seconds": seconds, "weight_model": row["weight_model"], "task": row["task"]})
    _write_csv(out / "benchmarks.csv", individual)
    _write_csv(out / "dijkstra_cases.csv", [{k: v for k, v in c.items() if not isinstance(v, list)} for c in pair_cases])
    (out / "parte2_report.json").write_text(json.dumps(_clean_json(payload), ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    return payload
