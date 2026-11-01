# [IA] OpenAI Codex: testes do contrato dos dados e dos artefatos offline.
from copy import deepcopy
from html.parser import HTMLParser
import json

from PIL import Image, ImageStat

from src.graphs.io import parse_map
from src.parte1 import solve_maze
from src.viz import prepare_interactive_data, render_part1


class EmbeddedData(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside = False
        self.parts = []
        self.external_resources = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and attrs.get("id") == "labirinto-data":
            self.inside = True
        for attr in ("src", "href"):
            if attrs.get(attr, "").startswith(("http:", "https:", "//")):
                self.external_resources.append(attrs[attr])

    def handle_endtag(self, tag):
        if tag == "script":
            self.inside = False

    def handle_data(self, text):
        if self.inside:
            self.parts.append(text)


def test_camadas_agrupam_bonus_mas_preservam_chaves_e_armadilhas():
    payload = {"manual": {"rows": ["#####", "#SaG#", "#####"], "states": {
        "inicio": {"row": 1, "col": 1, "keys": [], "bonus": []},
        "inicio_com_bonus": {"row": 1, "col": 1, "keys": [], "bonus": [0]},
        "chave": {"row": 1, "col": 2, "keys": ["a"], "bonus": []},
    }, "solutions": {}, "traps": ["inicio_com_bonus"], "metrics": {}}}
    original = deepcopy(payload)
    data = prepare_interactive_data(payload)["maps"][0]
    assert len(data["layers"]) == 2
    empty, key = data["layers"]
    assert empty["keys"] == []
    assert empty["cells"] == [{"row": 1, "col": 1, "states": 2, "traps": 1}]
    assert key["keys"] == ["a"] and key["traps"] == 0
    assert sum(layer["states"] for layer in data["layers"]) == data["state_count"] == 3
    assert sum(layer["traps"] for layer in data["layers"]) == data["trap_count"] == 1
    assert payload == original


def test_exportacao_offline_preserva_trace_e_escapa_dados(tmp_path):
    sample = solve_maze(parse_map("#######\n#S.aAG#\n#######", name="manual"))
    sample["metrics"]["non_finite"] = float("-inf")
    name = "manual </script><script>alert('teste')</script>"
    render_part1({name: sample}, tmp_path)
    exported = json.loads((tmp_path / "dados_interativo.json").read_text(encoding="utf-8"))
    parser = EmbeddedData()
    parser.feed((tmp_path / "labirinto_interativo.html").read_text(encoding="utf-8"))
    embedded = json.loads("".join(parser.parts))
    assert embedded == exported
    assert embedded["maps"][0]["name"] == name
    assert embedded["maps"][0]["solutions"]["BFS"]["trace"] == sample["solutions"]["BFS"]["trace"]
    assert embedded["maps"][0]["metrics"]["non_finite"] == "−∞"
    assert not parser.external_resources


def test_render_gera_pngs_reais_e_conjunto_completo(tmp_path):
    sample = solve_maze(parse_map("#######\n#S.aAG#\n#######", name="manual"))
    written = render_part1({"m02_manual": sample, "m03_manual": sample, "m08_manual": sample}, tmp_path)
    required = {"percurso_m03.png", "percurso_m08.png", "camadas_m02.png", "arvore_bfs_m02.png",
                "heatmap_m08.png", "dados_interativo.json", "labirinto_interativo.html"}
    assert {path.name for path in written} == required
    for path in written:
        if path.suffix == ".png":
            with Image.open(path) as image:
                assert image.format == "PNG"
                assert image.width >= 900 and image.height >= 500
                assert max(ImageStat.Stat(image.convert("RGB")).var) > 100
