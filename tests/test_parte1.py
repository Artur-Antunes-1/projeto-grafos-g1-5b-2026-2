# [IA] OpenAI Codex - testes de integração da Parte 1.
from src.graphs.io import parse_map
from src.graphs.estados import build_state_graph
from src.parte1 import graph_metrics, solve_maze, write_json


def test_metricas_excluem_alvo_e_arco_virtual():
    maze = parse_map('#######\n#S.aAG#\n#######', name='manual')
    graph, source, states = build_state_graph(maze)
    metrics = graph_metrics(graph, set(states))
    assert len(states) == 7
    assert metrics['order'] == 7
    assert metrics['size'] == 10
    assert metrics['density'] == 10 / 42


def test_passos_e_custo_nao_contam_arco_virtual():
    result = solve_maze(parse_map('#######\n#S.aAG#\n#######', name='manual'))
    assert result['solutions']['BFS']['steps'] == 4
    assert result['solutions']['DIJKSTRA']['cost'] == 4
    assert result['solutions']['BFS']['trace'][0]['cost'] == 0
    assert result['solutions']['BFS']['trace'][-1]['col'] == 5


def test_sem_solucao_nao_gera_caminho_falso():
    import json
    result = solve_maze(parse_map('#######\n#S#..G#\n#######', name='fechado'))
    assert result['solutions']['BFS']['status'] == 'SEM_SOLUCAO'
    assert result['solutions']['BFS']['path'] == []
    assert result['traps'] == ['(1,1)|-|{}']
    json.dumps(result, allow_nan=False)


def test_exportacao_json_nao_aceita_infinito(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        write_json(tmp_path / 'invalido.json', {'tempo': float('inf')})
