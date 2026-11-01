# [IA] OpenAI Codex: implementação integral das visualizações e da interface.
"""Figuras dos labirintos e interface offline sobre resultados já calculados.

Este módulo não resolve caminhos: consome o contrato de ``run_part1``. Uma
camada é um conjunto de chaves; variantes de bônus continuam na mesma camada.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import json
import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import MaxNLocator
import numpy as np


LAYER_COLORS = ["#166b9f", "#b85b15", "#21805c", "#8a4baf", "#b92e57", "#517323",
                "#007e86", "#765c36", "#4d5fb9", "#a53c1f", "#527c88", "#7d3983",
                "#59656e", "#996b00", "#ae477b", "#2b6d47"]
CELL_COLORS = ["#304756", "#f8fbfc", "#e1c9a0", "#b8d8e9", "#f6da79", "#cbbbe0",
               "#d6e9e5", "#ffe99c", "#e5c7ed", "#b8e2ce", "#bed8ef"]


def _keys(state: dict) -> tuple:
    return tuple(sorted(state.get("keys", [])))


def _layer_name(keys: tuple | list) -> str:
    return "Sem chaves" if not keys else "Chaves: " + ", ".join(str(key) for key in keys)


def _safe_json(value: Any) -> Any:
    """JSON válido inclusive quando um custo é infinito ou indefinido."""
    if isinstance(value, float) and not math.isfinite(value):
        return "−∞" if value < 0 else ("∞" if value > 0 else "indefinido")
    if isinstance(value, dict):
        return {str(k): _safe_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_safe_json(v) for v in value]
    return value


def prepare_interactive_data(payload: dict) -> dict:
    """Compacta estados por casa/camada sem perder multiplicidade ou armadilhas.

    Os percursos e custos são copiados dos resultados Python. O navegador só
    seleciona quadros e desenha os agregados; não calcula buscas ou caminhos.
    """
    maps = []
    for name, item in sorted(payload.items()):
        states = item.get("states", {})
        traps = set(item.get("traps", []))
        groups = defaultdict(lambda: defaultdict(lambda: {"states": 0, "traps": 0}))
        for label, state in states.items():
            keyset = _keys(state)
            cell = groups[keyset][(state["row"], state["col"])]
            cell["states"] += 1
            cell["traps"] += label in traps
        layers = []
        for keyset, cells in sorted(groups.items(), key=lambda pair: (len(pair[0]), pair[0])):
            layers.append({
                "id": "".join(str(k) for k in keyset), "keys": list(keyset),
                "label": _layer_name(keyset),
                "states": sum(cell["states"] for cell in cells.values()),
                "traps": sum(cell["traps"] for cell in cells.values()),
                "cells": [{"row": r, "col": c, **cell} for (r, c), cell in sorted(cells.items())],
            })
        maps.append({"name": name, "rows": item["rows"], "layers": layers,
                     "solutions": item.get("solutions", {}), "metrics": item.get("metrics", {}),
                     "state_count": len(states), "trap_count": len(traps & states.keys())})
    return _safe_json({"schema_version": 1, "maps": maps})


def _cell_type(char: str) -> int:
    if char == "#":
        return 0
    if char == ",":
        return 2
    if char == "~":
        return 3
    if char in "abcdef":
        return 4
    if char in "ABCDEF":
        return 5
    if char in "^v<>":
        return 6
    return {"+": 7, "*": 8, "S": 9, "G": 10}.get(char, 1)


def _map_axes(ax, rows: list[str], *, symbols: bool = True) -> None:
    image = np.array([[_cell_type(char) for char in row] for row in rows])
    ax.imshow(image, cmap=ListedColormap(CELL_COLORS), vmin=0, vmax=len(CELL_COLORS) - 1,
              interpolation="nearest", origin="upper")
    height, width = len(rows), len(rows[0])
    if symbols:
        for r, row in enumerate(rows):
            for c, char in enumerate(row):
                if char not in "#.,~ ":
                    ax.text(c, r, char, ha="center", va="center", color="#15334a",
                            fontsize=8 if width > 40 else 11, weight="bold", zorder=6)
    step = 5 if width > 40 else 2
    ax.set_xticks(range(0, width, step))
    ax.set_yticks(range(0, height, 5 if height > 20 else 1))
    ax.set_xlabel("Coluna (base zero)")
    ax.set_ylabel("Linha (base zero)")
    ax.set_xlim(-0.5, width - 0.5)
    ax.set_ylim(height - 0.5, -0.5)
    ax.set_aspect("equal")


def _save(fig, path: Path) -> None:
    fig.savefig(path, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _solution(item: dict) -> tuple[str, dict]:
    solutions = item.get("solutions", {})
    for preferred in ("dijkstra", "bellman_ford", "bellman-ford", "bfs", "dfs"):
        for name, solution in solutions.items():
            if name.lower() == preferred and solution.get("trace"):
                if str(solution.get("status", "OK")).upper() not in {"CICLO_NEGATIVO", "RECUSA", "SEM_SOLUCAO"}:
                    return name, solution
    return "", {}


def _plot_route(name: str, item: dict, path: Path) -> None:
    rows = item["rows"]
    width, height = len(rows[0]), len(rows)
    fig, ax = plt.subplots(figsize=(max(11, width * .22), max(5, height * .22)))
    _map_axes(ax, rows)
    algorithm, solution = _solution(item)
    trace = solution.get("trace", [])
    keysets = sorted({_keys(state) for state in trace}, key=lambda x: (len(x), x))
    colors = {keys: LAYER_COLORS[i % len(LAYER_COLORS)] for i, keys in enumerate(keysets)}
    if len(trace) > 1:
        physical_edges = defaultdict(set)
        route = []
        for a, b in zip(trace, trace[1:]):
            source, target = (a["col"], a["row"]), (b["col"], b["row"])
            edge = tuple(sorted((source, target)))
            physical_edges[edge].add(_keys(b))
            route.append((edge, _keys(b)))
        # Repassagens são deslocadas lateralmente para não apagar as cores das
        # camadas anteriores na mesma aresta física (especialmente em m03).
        segments, segment_colors = [], []
        for edge, keys in route:
            ordered = sorted(physical_edges[edge], key=lambda value: (len(value), value))
            offset = (ordered.index(keys) - (len(ordered) - 1) / 2) * .17
            (x1, y1), (x2, y2) = edge
            length = math.hypot(x2 - x1, y2 - y1) or 1
            dx, dy = -(y2 - y1) / length * offset, (x2 - x1) / length * offset
            segments.append([(x1 + dx, y1 + dy), (x2 + dx, y2 + dy)])
            segment_colors.append(colors[keys])
        ax.add_collection(LineCollection(segments, colors="white", linewidths=4.7, zorder=3))
        ax.add_collection(LineCollection(segments, colors=segment_colors, linewidths=2.6, zorder=4))
        for previous, state in zip(trace, trace[1:]):
            if _keys(previous) != _keys(state):
                ax.scatter(state["col"], state["row"], marker="o", s=85,
                           facecolors="none", edgecolors=colors[_keys(state)], linewidths=2, zorder=7)
    if trace:
        ax.scatter(trace[0]["col"], trace[0]["row"], s=120, marker="s", facecolors="none",
                   edgecolors="#15334a", linewidths=2, zorder=8)
        ax.scatter(trace[-1]["col"], trace[-1]["row"], s=160, marker="*", facecolors="none",
                   edgecolors="#15334a", linewidths=1.8, zorder=8)
    else:
        ax.text(.5, -.16, "Nenhum percurso finito disponível neste resultado.", transform=ax.transAxes,
                ha="center", color="#8d243b")
    shown = algorithm.replace("_", " ").title()
    summary = f"{shown}: {solution.get('steps', '—')} passos; custo {solution.get('cost', '—')}" if trace else "Sem percurso"
    ax.set_title(f"{name} — percurso por conjunto de chaves\n{summary}", loc="left", pad=14, weight="bold")
    handles = [Line2D([0], [0], color=colors[keys], lw=3, label=_layer_name(keys)) for keys in keysets]
    handles.extend([Patch(facecolor=CELL_COLORS[0], label="Parede"),
                    Patch(facecolor=CELL_COLORS[2], label="Lama (,)"),
                    Patch(facecolor=CELL_COLORS[3], label="Água (~)"),
                    Line2D([0], [0], marker="o", color="none", markeredgecolor="#15334a", label="Coleta de chave")])
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(.5, -.13), ncol=min(4, len(handles)),
              frameon=False, fontsize=9)
    _save(fig, path)


def _plot_layers(name: str, item: dict, path: Path) -> None:
    states = item.get("states", {})
    groups = sorted({_keys(state) for state in states.values()}, key=lambda x: (len(x), x))
    layer_index = {keys: i for i, keys in enumerate(groups)}
    rows = item["rows"]
    width, height = len(rows[0]), len(rows)
    positions = {}
    duplicates = defaultdict(list)
    for label, state in sorted(states.items()):
        duplicates[(_keys(state), state["row"], state["col"])].append(label)
    for (keys, r, c), labels in duplicates.items():
        for i, label in enumerate(labels):
            angle = 2 * math.pi * i / len(labels)
            radius = .15 if len(labels) > 1 else 0
            positions[label] = (c + layer_index[keys] * (width + 4) + radius * math.cos(angle),
                                r + radius * math.sin(angle))
    fig, ax = plt.subplots(figsize=(max(12, len(groups) * 7), max(5.5, height * .8)))
    for i, keys in enumerate(groups):
        offset = i * (width + 4)
        ax.add_patch(Rectangle((offset - .6, -.8), width + .2, height + .3,
                               facecolor="#f5f8fa", edgecolor="#b6c6d0", zorder=0))
        ax.text(offset + (width - 1) / 2, -1.25, _layer_name(keys), ha="center", weight="bold",
                color=LAYER_COLORS[i % len(LAYER_COLORS)])
    for edge in item.get("edges", []):
        source, target = edge["source"], edge["target"]
        if source not in positions or target not in positions:
            continue
        cross = _keys(states[source]) != _keys(states[target])
        ax.annotate("", positions[target], positions[source],
                    arrowprops={"arrowstyle": "-|>", "color": "#b85b15" if cross else "#8c9eaa",
                                "alpha": .85 if cross else .6, "lw": 1.5 if cross else .65,
                                "connectionstyle": "arc3,rad=.1", "shrinkA": 5, "shrinkB": 5}, zorder=1)
    for keys in groups:
        labels = [label for label, state in states.items() if _keys(state) == keys]
        ax.scatter([positions[label][0] for label in labels], [positions[label][1] for label in labels],
                   c=LAYER_COLORS[layer_index[keys] % len(LAYER_COLORS)], s=90, edgecolors="white", zorder=3)
        for label in labels:
            x, y = positions[label]
            state = states[label]
            ax.annotate(f"{state['row']},{state['col']}", (x, y), (0, -12), textcoords="offset points",
                        ha="center", fontsize=6.5, color="#15334a", zorder=4)
    ax.set_title(f"{name} — grafo de estados em camadas\nCada nó é um estado; a posição segue a casa do mapa. ALVO omitido.",
                 loc="left", pad=26, weight="bold")
    ax.set_xlabel("Coluna do mapa + deslocamento da camada")
    ax.set_ylabel("Linha do mapa (base zero)")
    ticks = [i * (width + 4) + c for i in range(len(groups)) for c in range(0, width, 2)]
    ax.set_xticks(ticks, [str(c) for _ in groups for c in range(0, width, 2)])
    ax.set_yticks(range(height))
    ax.set_ylim(height + .2, -2)
    ax.set_aspect("equal")
    ax.legend(handles=[Line2D([0], [0], color="#8c9eaa", label="Arco dentro da camada"),
                       Line2D([0], [0], color="#b85b15", lw=2, label="Coleta: arco para outra camada")],
              loc="upper center", bbox_to_anchor=(.5, -.15), ncol=2, frameon=False)
    _save(fig, path)


def _plot_bfs_tree(name: str, item: dict, path: Path) -> None:
    states = item.get("states", {})
    parents = {label: parent for label, parent in item.get("bfs_parent", {}).items() if label in states}
    distance = item.get("bfs_distance", {})
    fig, ax = plt.subplots(figsize=(15, 11))
    if not parents or not distance:
        ax.text(.5, .5, "Árvore indisponível: fornecer bfs_parent e bfs_distance do resultado BFS.",
                ha="center", transform=ax.transAxes)
        ax.set_axis_off()
        _save(fig, path)
        return
    children = defaultdict(list)
    roots = []
    for label, parent in parents.items():
        if parent in parents:
            children[parent].append(label)
        else:
            roots.append(label)
    for labels in children.values():
        labels.sort()
    # Layout de árvore pelos pais fornecidos; nenhuma nova busca no grafo.
    traversal = []
    stack = sorted(roots, reverse=True)
    seen = set()
    while stack:
        label = stack.pop()
        if label in seen:
            continue
        seen.add(label)
        traversal.append(label)
        stack.extend(reversed(children[label]))
    positions = {}
    next_leaf = 0
    for label in reversed(traversal):
        laid_children = [child for child in children[label] if child in positions]
        if laid_children:
            x = sum(positions[child][0] for child in laid_children) / len(laid_children)
        else:
            x = next_leaf
            next_leaf += 1
        positions[label] = (x, distance.get(label, 0))
    segments = [[positions[parent], positions[label]] for label, parent in parents.items()
                if label in positions and parent in positions]
    ax.add_collection(LineCollection(segments, colors="#9caeb9", linewidths=.85, zorder=1))
    groups = sorted({_keys(states[label]) for label in positions}, key=lambda x: (len(x), x))
    color_index = {keys: i for i, keys in enumerate(groups)}
    for label, (x, y) in positions.items():
        ax.scatter(x, y, s=65, c=LAYER_COLORS[color_index[_keys(states[label])]], edgecolors="white", zorder=3)
        state = states[label]
        if len(positions) <= 160:
            ax.annotate(f"({state['row']},{state['col']})", (x, y), (7, 0), textcoords="offset points",
                        va="center", fontsize=7, color="#15334a")
    ax.set_xlim(-.35, max(next_leaf - 1, 1) + .75)
    max_depth = max((pos[1] for pos in positions.values()), default=0)
    fig.set_size_inches(max(8, min(16, 4 + next_leaf * 2)), max(7, min(14, (max_depth + 3) * .3)))
    ax.set_ylim(max_depth + 1, -1)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=15))
    ax.set_xlabel("Ramos da árvore (posição horizontal usada apenas para separar ramos)")
    ax.set_ylabel("Distância BFS em passos desde S")
    ax.set_xticks([])
    ax.grid(axis="y", alpha=.15)
    ax.set_title(f"{name} — árvore de descoberta BFS\nSomente arcos pai–filho; rótulos indicam (linha, coluna); ALVO omitido.",
                 loc="left", pad=18, weight="bold")
    ax.legend(handles=[Line2D([0], [0], marker="o", lw=0, color=LAYER_COLORS[i], label=_layer_name(keys))
                       for i, keys in enumerate(groups)], frameon=False, loc="upper right")
    _save(fig, path)


def _plot_heatmap(name: str, item: dict, path: Path) -> None:
    rows = item["rows"]
    height, width = len(rows), len(rows[0])
    counts = Counter((state["row"], state["col"]) for state in item.get("states", {}).values())
    values = np.array([[float("nan") if char == "#" else counts[(r, c)] for c, char in enumerate(row)]
                       for r, row in enumerate(rows)])
    fig, ax = plt.subplots(figsize=(max(12, width * .22), max(6, height * .23)))
    cmap = plt.get_cmap("cividis").with_extremes(bad=CELL_COLORS[0])
    picture = ax.imshow(values, origin="upper", cmap=cmap, vmin=0, interpolation="nearest")
    for r, row in enumerate(rows):
        for c, char in enumerate(row):
            if char in "SGabcdefABCDEF":
                ax.text(c, r, char, ha="center", va="center", fontsize=7, weight="bold", color="white",
                        bbox={"facecolor": "#15334a", "alpha": .85, "pad": .3, "edgecolor": "none"})
    colorbar = fig.colorbar(picture, ax=ax, fraction=.025, pad=.025)
    colorbar.set_label("Estados alcançáveis na casa (chaves e bônus)")
    colorbar.locator = MaxNLocator(integer=True, nbins=8)
    colorbar.update_ticks()
    ax.set_xticks(range(0, width, 5 if width > 40 else 2))
    ax.set_yticks(range(0, height, 5 if height > 20 else 1))
    ax.set_xlabel("Coluna (base zero)")
    ax.set_ylabel("Linha (base zero)")
    ax.set_title(f"{name} — multiplicidade de estados por casa\nCada estado é contado uma vez, independentemente do percurso; ALVO excluído.",
                 loc="left", pad=15, weight="bold")
    ax.legend(handles=[Patch(facecolor=CELL_COLORS[0], label="Parede"),
                       Patch(facecolor=cmap(0), label="0: casa sem estado alcançável")],
              loc="upper center", bbox_to_anchor=(.5, -.12), ncol=2, frameon=False)
    _save(fig, path)


def render_part1(payload: dict, out: str | Path) -> list[Path]:
    """Gera as figuras disponíveis e um HTML independente de servidor/CDN.

    ``payload`` segue docs/PLANO_IMPLEMENTACAO.md. Para a árvore são usados os
    opcionais ``bfs_parent`` e ``bfs_distance`` do BFS já executado pelo chamador.
    ``out`` pode conter outras exportações: apenas estes arquivos são escritos.
    """
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.titlecolor": "#15334a", "text.color": "#15334a"}):
        for prefix, filename, draw in [("m03", "percurso_m03.png", _plot_route),
                                       ("m08", "percurso_m08.png", _plot_route),
                                       ("m02", "camadas_m02.png", _plot_layers),
                                       ("m02", "arvore_bfs_m02.png", _plot_bfs_tree),
                                       ("m08", "heatmap_m08.png", _plot_heatmap)]:
            match = next(((name, item) for name, item in sorted(payload.items()) if name.startswith(prefix)), None)
            if match:
                path = out / filename
                draw(*match, path)
                written.append(path)
    interactive = prepare_interactive_data(payload)
    serialized = json.dumps(interactive, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    data_path = out / "dados_interativo.json"
    data_path.write_text(serialized + "\n", encoding="utf-8")
    # Evita fechar a tag script caso um nome ou metadado contenha texto HTML.
    embedded = serialized.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    template = (Path(__file__).parent / "templates" / "labirinto.html").read_text(encoding="utf-8")
    html_path = out / "labirinto_interativo.html"
    html_path.write_text(template.replace("__LABIRINTO_DATA__", embedded), encoding="utf-8")
    return written + [data_path, html_path]
