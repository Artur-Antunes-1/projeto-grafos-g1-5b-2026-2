# [IA] OpenAI Codex - geração assistida de testes da validação de mapas.
import pytest

from src.graphs.io import parse_map, read_map


@pytest.mark.parametrize("text, message", [
    ("S.\n..G", "retangular"), ("SSG", "exatamente um S"),
    ("...G", "exatamente um S"), ("S..", "pelo menos um G"),
    ("S?G", "símbolo"), ("; só comentário\n", "vazio"),
])
def test_invalid_maps_fail_clearly(text, message):
    with pytest.raises(ValueError, match=message):
        parse_map(text)


def test_parse_comments_blank_lines_and_reading_order_metadata(tmp_path):
    text = "; comentário\n\n#######\n#Sa+G*#\n#b.+G*#\n#######\n"
    path = tmp_path / "exemplo.txt"
    path.write_text(text, encoding="utf-8")
    maze = read_map(path)
    assert maze.name == "exemplo"
    assert maze.start == (1, 1)
    assert maze.goals == ((1, 4), (2, 4))
    assert maze.keys == frozenset({"a", "b"})
    assert maze.bonus_positions == ((1, 3), (2, 3))
    assert maze.source_positions == ((1, 5), (2, 5))
    assert len(maze.rows) == 4


def test_whitespace_inside_grid_is_not_silently_removed():
    with pytest.raises(ValueError, match="símbolo"):
        parse_map("S G")
