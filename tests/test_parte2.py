# [IA] Testes escritos com assistência integral de IA; não atribuem autoria humana.
import csv
import math
from pathlib import Path

import pytest

from src.graphs.algorithms import bellman_ford, bfs, dijkstra
from src.graphs.graph import DirectedGraph
from src.parte2 import (
    Rating,
    build_rating_graph,
    increasing_layer_dag,
    nested_induced_graphs,
    path_weight,
    read_ratings,
    run_part2,
    select_sources,
    summarize_times,
)


def test_rating_objectives_are_distinct_and_nonnegative():
    records = [Rating(1, 2, -10, 100), Rating(2, 3, 10, 200), Rating(1, 3, 1, 300)]
    original = build_rating_graph(records)
    costs = build_rating_graph(records, transformed=True)
    assert list(original.edges()) == [(1, 2, -10), (1, 3, 1), (2, 3, 10)]
    assert all(w >= 0 for _, _, w in costs.edges())
    assert path_weight(original, [1, 2, 3]) == 0
    assert path_weight(costs, [1, 2, 3]) == 20
    assert dijkstra(costs, 1)["distance"][3] == 9
    with pytest.raises(ValueError, match="arco"):
        path_weight(original, [3, 1])


def test_layer_control_retains_real_negative_edges_and_breaks_cycles():
    original = build_rating_graph([
        Rating(1, 2, -4, 0), Rating(2, 3, -3, 0),
        Rating(3, 1, 1, 0), Rating(2, 1, 1, 0),
    ])
    control, layers = increasing_layer_dag(original, 1)
    assert layers == {1: 0, 2: 1, 3: 2}
    assert set(control.edges()) == {(1, 2, -4), (2, 3, -3)}
    result = bellman_ford(control, 1)
    assert result["negative_cycle"] == []
    assert result["distance"][3] == -7
    assert bellman_ford(original, 1)["negative_cycle"]


def test_nested_samples_include_isolated_selected_vertices():
    graph = DirectedGraph()
    for node in range(20):
        graph.add_node(node)
    graph.add_edge(1, 2, -1)
    samples = nested_induced_graphs(graph)
    nodes = [set(item["graph"].adj) for item in samples]
    assert [len(n) for n in nodes] == [2, 10, 20]
    assert nodes[0] <= nodes[1] <= nodes[2]
    assert nodes == [set(i["graph"].adj) for i in nested_induced_graphs(graph)]
    for item in samples:
        chosen = set(item["graph"].adj)
        assert set(item["graph"].edges()) == {
            edge for edge in graph.edges() if edge[0] in chosen and edge[1] in chosen
        }


def test_input_preserves_row_count_and_describes_missing_values(tmp_path):
    path = tmp_path / "ratings.csv"
    path.write_text(",SOURCE,TARGET,RATING,TIME\n0,1,2,-2,100\n1,2,1,0,200\n", encoding="utf-8")
    records, meta = read_ratings(path)
    assert len(records) == 2
    assert meta["rows"] == 2 and meta["nodes"] == 2
    assert meta["missing_by_column"] == {"SOURCE": 0, "TARGET": 0, "RATING": 0, "TIME": 0}
    assert meta["sign_counts"] == {"negative": 1, "zero": 1, "positive": 0}
    assert meta["sha256"]
    path.write_text("SOURCE,TARGET,RATING,TIME\n1,2,,100\n", encoding="utf-8")
    with pytest.raises(ValueError, match="ausente"):
        read_ratings(path)


@pytest.mark.parametrize("rating", [-11, 11])
def test_input_rejects_outside_rating_scale(tmp_path, rating):
    path = tmp_path / "invalid.csv"
    path.write_text(f"SOURCE,TARGET,RATING,TIME\n1,2,{rating},100\n", encoding="utf-8")
    with pytest.raises(ValueError, match="-10"):
        read_ratings(path)


def test_sources_and_time_statistics_are_deterministic():
    graph = build_rating_graph([Rating(1, 2, 1, 0), Rating(1, 3, -1, 0), Rating(2, 3, 3, 0)])
    assert len(select_sources(graph)) == 3
    stats = summarize_times([1.0, 2.0, 3.0, 4.0, 5.0])
    assert stats["repetitions"] == 5
    assert stats["median_seconds"] == 3
    assert stats["mean_seconds"] == 3
    assert stats["min_seconds"] == 1 and stats["max_seconds"] == 5


def test_isolated_source_layer_control_is_valid():
    graph = DirectedGraph()
    graph.add_node(5)
    graph.add_node(8)
    dag, layers = increasing_layer_dag(graph, 5)
    assert set(dag.adj) == {5}
    assert layers == {5: 0}
    assert bellman_ford(dag, 5)["distance"][5] == 0


def test_alternative_csv_does_not_inherit_received_copy_provenance(tmp_path):
    path = tmp_path / "alternative.csv"
    path.write_text("SOURCE,TARGET,RATING,TIME\n101,102,-2,100\n102,101,0,200\n", encoding="utf-8")
    _, metadata = read_ratings(path)
    assert metadata["rows"] == 2 and metadata["nodes"] == 2
    assert "não comparada" in metadata["version_note"]
    assert metadata["is_known_received_csv"] is False
    assert "registro ausente" not in metadata["version_note"]
    assert "24185" not in metadata["version_note"]


def test_known_received_csv_provenance_requires_exact_hash():
    path = Path(__file__).resolve().parents[1] / "data/dataset_parte2/bitcoinalpha.csv"
    _, metadata = read_ratings(path)
    assert metadata["sha256"] == "d2f121d67f325ba2dfbbf0e9708843d7c9b0f898494957fb6b1b239db5150c8a"
    assert metadata["is_known_received_csv"] is True
    assert "registro ausente" in metadata["version_note"]


@pytest.fixture
def alternative_report(tmp_path):
    path = tmp_path / "other_version.csv"
    path.write_text(
        "SOURCE,TARGET,RATING,TIME\n101,102,-1,100\n102,103,-1,200\n"
        "103,104,-1,300\n104,105,-1,400\n105,101,-1,500\n101,103,-1,600\n",
        encoding="utf-8",
    )
    out = tmp_path / "results"
    return run_part2(tmp_path, out, repetitions=5, render=False, dataset=path), out, path


def test_alternative_report_notes_follow_actual_graph(alternative_report):
    report, out, _ = alternative_report
    notes = (out / "notas_analiticas.md").read_text(encoding="utf-8")
    analysis = (out / "analise.md").read_text(encoding="utf-8")
    top = report["structure"]["top_in_degree"][0]
    assert f"O usuário {top['node']} tem maior entrada ({top['in_degree']})" in notes
    for traversal in report["traversals"]:
        assert f"fonte {traversal['source']}: {traversal['reachable']} alcançáveis, {traversal['unreachable']} inalcançáveis, profundidade máxima {traversal['max_distance']}" in notes
    for sample in (b for b in report["benchmarks"] if b["algorithm"] == "BFS"):
        assert f"{sample['nodes']}/{sample['edges']}" in notes
    assert "Dijkstra usa mais arcos em 0" in notes
    assert "não comparada" in notes and "não comparada" in analysis
    assert "registro ausente" not in notes and "difere da versão original SNAP por um registro" not in analysis
    assert "3748" not in notes and "3782/24185" not in notes
    assert "positivas predominam" not in notes


def test_ratings_figure_explains_all_three_signal_colors(alternative_report, monkeypatch):
    import matplotlib.figure
    from src.parte2 import _metrics, _render
    report, out, path = alternative_report
    records, _ = read_ratings(path)
    nodes, _ = _metrics(build_rating_graph(records), records)
    legends = {}

    def inspect_legend(figure, path, **kwargs):
        legends[Path(path).stem] = [
            text.get_text() for axis in figure.axes
            if axis.get_legend() for text in axis.get_legend().get_texts()
        ]

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", inspect_legend)
    _render(report, records, nodes, out)
    assert set(legends["exploratoria_01_ratings"]) == {"Negativo", "Zero", "Positivo"}
    assert legends["explanatoria_02_ciclo"]
    assert legends["comparacao_algoritmos"]
