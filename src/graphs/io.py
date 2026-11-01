# [IA] OpenAI Codex - geração assistida da leitura e validação de mapas.
"""IO de mapas: validação explícita antes da construção dos grafos."""

from dataclasses import dataclass
from pathlib import Path

Position = tuple[int, int]
ALLOWED_SYMBOLS = frozenset("#.SG,~abcdABCD><^v+*")


@dataclass(frozen=True, slots=True)
class Maze:
    name: str
    rows: list[str]
    start: Position
    goals: tuple[Position, ...]
    keys: frozenset[str]
    bonus_positions: tuple[Position, ...]
    source_positions: tuple[Position, ...]


def parse_map(text: str, name: str = "mapa") -> Maze:
    """Lê grade com coordenadas base zero, ignorando linhas vazias e ';'.

    Espaços dentro de linhas da grade são inválidos. Nenhum símbolo da grade
    é removido para esconder erros de largura ou caracteres desconhecidos.
    """
    rows = [line for line in text.lstrip("\ufeff").splitlines() if line and not line.startswith(";")]
    if not rows:
        raise ValueError(f"Mapa {name!r} vazio: nenhuma linha de grade.")
    width = len(rows[0])
    if any(len(line) != width for line in rows):
        raise ValueError(f"Mapa {name!r} não é retangular: as linhas têm larguras diferentes.")
    positions = {}
    for row, line in enumerate(rows):
        for col, symbol in enumerate(line):
            if symbol not in ALLOWED_SYMBOLS:
                raise ValueError(f"Mapa {name!r}: símbolo desconhecido {symbol!r} em ({row},{col}).")
            positions.setdefault(symbol, []).append((row, col))
    starts = positions.get("S", [])
    if len(starts) != 1:
        raise ValueError(f"Mapa {name!r} deve ter exatamente um S; encontrados {len(starts)}.")
    goals = tuple(positions.get("G", []))
    if not goals:
        raise ValueError(f"Mapa {name!r} deve ter pelo menos um G.")
    return Maze(
        name=name, rows=rows, start=starts[0], goals=goals,
        keys=frozenset(symbol for symbol in "abcd" if symbol in positions),
        bonus_positions=tuple(positions.get("+", [])),
        source_positions=tuple(positions.get("*", [])),
    )


def read_map(path: str | Path) -> Maze:
    path = Path(path)
    return parse_map(path.read_text(encoding="utf-8-sig"), name=path.stem)
