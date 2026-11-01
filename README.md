# Projeto de Teoria dos Grafos — G1 / 5B

Projeto final de Teoria dos Grafos e Análise e Visualização de Dados (AVD), semestre 2026.2.

## Integrantes

- Artur Antunes
- Ricardo Machado
- Victor Uen
- Luca Ribeiro
- Pedro Ferraz

## Estado atual

Estrutura inicial do repositório, mapas fornecidos, dataset e orientações da professora organizados. A implementação, os testes dos algoritmos, os experimentos e o relatório técnico ainda serão desenvolvidos pelo grupo.

O dataset escolhido é o **Bitcoin Alpha**. Artur informou que a escolha já foi aprovada pelas duas professoras. A proposta aprovada deve ser arquivada em `docs/` pelo grupo.

## Organização

```text
data/
  mapas/             oito mapas fornecidos
  mapas_grupo/       dois mapas a criar pelo grupo
  dataset_parte2/    CSV recebido e sua procedência
src/
  graphs/            estrutura do grafo, IO e algoritmos a implementar
tests/               testes a escrever pelo grupo
out/
  parte1/            resultados dos labirintos a gerar
  parte2/            experimentos e visualizações a gerar
docs/
  referencias/       PDFs originais da professora
  CHECKLIST.md       entregas exigidas e pendências
  CONTRIBUICOES.md   pacotes e registro de contribuições
  REGISTRO_IA.md     apoio de IA utilizado nesta preparação
```

Os módulos previstos no enunciado são `src/cli.py`, `src/solve.py`, `src/viz.py`, `src/graphs/io.py`, `estados.py`, `graph.py` e `algorithms.py`. Eles ainda não foram implementados.

## Preparação do ambiente

Python **3.11 ou superior**. No PowerShell, com Python instalado:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

As dependências iniciais são pytest, pandas e matplotlib. A interface de execução será documentada quando existir. Ainda não há aplicação ou testes executáveis neste repositório.

## Materiais e dados

- As regras e a rubrica originais estão em `docs/referencias/`.
- Os oito mapas foram copiados do ZIP fornecido, preservando seu conteúdo.
- O CSV em `data/dataset_parte2/` preserva o arquivo recebido. Há uma diferença de um registro em relação à fonte SNAP; os detalhes estão no README da pasta. O grupo deve registrar qual versão utilizará nos experimentos.
- Fonte do dataset: [Bitcoin Alpha — Stanford SNAP](https://snap.stanford.edu/data/soc-sign-bitcoin-alpha.html).
- Os hashes e a procedência dos materiais estão em `docs/PROVENIENCIA.json`.

## Trabalho do grupo

Cada pacote terá um dono e um revisor definidos pelo grupo. Todos devem ter contribuições reais em pelo menos dois pacotes e conhecer o projeto inteiro. A distribuição ainda está em aberto em `docs/CONTRIBUICOES.md`.

A IA foi usada na preparação desta estrutura, conforme `docs/REGISTRO_IA.md`. O núcleo dos algoritmos, a construção do grafo de estados, a resolução dos mapas e as decisões e interpretações autorais ficam a cargo do grupo, seguindo as orientações da disciplina. `networkx` só pode ser usado em `tests/`, como oráculo.

Entrega indicada nos materiais: **26/11/2026**, por todos os integrantes, via Classroom. A apresentação da turma 5B está indicada para **01/12/2026**, sujeita à organização da professora.
