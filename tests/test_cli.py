# [IA] OpenAI Codex - testes da interface de execução.
from src.cli import main


def test_cli_mapa_exporta_custo_e_percurso(tmp_path):
    import json
    maze = tmp_path / 'mapa.txt'
    maze.write_text('#####\n#S.G#\n#####', encoding='utf-8')
    out = tmp_path / 'resultados'
    assert main(['--mapa', str(maze), '--alg', 'BFS', '--out', str(out)]) == 0
    result = json.loads((out / 'solucao_mapa_BFS.json').read_text(encoding='utf-8'))
    assert result['steps'] == 2
    assert result['cost'] == 2


def test_cli_mapa_invalido_retorna_erro_claro(tmp_path, capsys):
    maze = tmp_path / 'invalido.txt'
    maze.write_text('S?', encoding='utf-8')
    assert main(['--mapa', str(maze)]) == 2
    assert 'Erro:' in capsys.readouterr().err


def test_cli_sem_origem_no_dataset_retorna_erro(tmp_path, capsys):
    path = tmp_path / 'dados.csv'
    path.write_text('SOURCE,TARGET,RATING,TIME\n1,2,5,100', encoding='utf-8')
    assert main(['--dataset', str(path), '--alg', 'DIJKSTRA']) == 2
    assert 'source' in capsys.readouterr().err


def test_cli_dataset_aceita_pasta_e_respeita_arquivo_informado(tmp_path):
    import json
    folder = tmp_path / 'dataset'
    folder.mkdir()
    (folder / 'bitcoinalpha.csv').write_text('SOURCE,TARGET,RATING,TIME\n101,202,5,100', encoding='utf-8')
    out = tmp_path / 'out'
    assert main(['--dataset', str(folder), '--alg', 'DIJKSTRA', '--source', '101', '--target', '202', '--out', str(out)]) == 0
    result = json.loads((out / 'consulta_DIJKSTRA_101.json').read_text(encoding='utf-8'))
    assert result['path'] == [101, 202]
    assert result['distance']['202'] == 5


def test_fonte_consumivel_nao_sobrescreve_arestas_do_mapa_original(tmp_path):
    maze = tmp_path / 'fonte.txt'
    maze.write_text('#####\n#S*G#\n#####', encoding='utf-8')
    out = tmp_path / 'out'
    command = ['--mapa', str(maze), '--alg', 'BELLMAN_FORD', '--out', str(out)]
    assert main(command) == 0
    original = (out / 'arestas_fonte.csv').read_bytes()
    assert main(command + ['--fonte-consumivel']) == 0
    assert (out / 'arestas_fonte.csv').read_bytes() == original
    assert (out / 'arestas_fonte_consumivel.csv').exists()


def test_bellman_ford_sem_destino_informa_ciclo_e_com_destino_respeita_affected(tmp_path):
    import json
    path = tmp_path / 'dados.csv'
    path.write_text('SOURCE,TARGET,RATING,TIME\n1,4,7,100\n1,2,0,100\n2,3,-2,100\n3,2,1,100', encoding='utf-8')
    out = tmp_path / 'out'
    command = ['--dataset', str(path), '--alg', 'BELLMAN_FORD', '--source', '1', '--out', str(out)]
    assert main(command) == 0
    result = json.loads((out / 'consulta_BELLMAN_FORD_1.json').read_text(encoding='utf-8'))
    assert result['status'] == 'CICLO_NEGATIVO'
    assert result['negative_cycle']
    assert main(command + ['--target', '4']) == 0
    result = json.loads((out / 'consulta_BELLMAN_FORD_1.json').read_text(encoding='utf-8'))
    assert result['status'] == 'OK'
    assert result['distance']['4'] == 7
    assert result['path'] == [1, 4]


def test_mapa_sem_arcos_exporta_cabecalho_csv_obrigatorio(tmp_path):
    import csv
    maze = tmp_path / 'isolado.txt'
    maze.write_text('#######\n#S#..G#\n#######', encoding='utf-8')
    out = tmp_path / 'out'
    assert main(['--mapa', str(maze), '--out', str(out)]) == 0
    with (out / 'arestas_isolado.csv').open(encoding='utf-8', newline='') as stream:
        rows = list(csv.reader(stream))
    assert rows == [['origem', 'destino', 'movimento', 'casa_destino', 'peso']]
