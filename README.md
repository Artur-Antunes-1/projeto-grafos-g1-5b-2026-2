# Teoria dos Grafos e AVD - G1 / 5B

Projeto final de 2026.2: labirintos com memória e análise da rede Bitcoin Alpha.

**Integrantes:** Artur Antunes, Ricardo Machado, Victor Uen, Luca Ribeiro e Pedro Ferraz.

Esta versão técnica foi desenvolvida integralmente com assistência de OpenAI Codex, por solicitação de Artur. Os algoritmos, análises, escolhas visuais e textos gerados por IA estão identificados. Esse uso ultrapassa os limites de IA definidos pela disciplina; a versão não deve ser declarada como produção autoral do grupo nem como entrega conforme essas regras. Contribuições humanas e assinaturas não foram simuladas.

## O que funciona

- Grafo dirigido próprio, validação de mapas, estados alcançáveis com chaves e bônus.
- BFS e DFS iterativas, Dijkstra com recusa de pesos negativos e Bellman-Ford com ciclo negativo e propagação dos vértices afetados.
- Oito mapas fornecidos, dois mapas do G1 e opção de fonte consumível para m06.
- Exportação das arestas, métricas sem ALVO, camadas, graus, percursos, armadilhas e comparações de modelagem.
- Interface HTML offline com animação, velocidade, avanço manual, seleção de algoritmo, camadas e armadilhas.
- Bitcoin Alpha com três fontes, nove pares de Dijkstra, dois casos Bellman-Ford, benchmarks de cinco execuções e três tamanhos.
- Cinco figuras da Parte 1, quatro exploratórias e duas explanatórias da Parte 2, mais dois gráficos de desempenho e notas analíticas.
- Relatório técnico/manual em PDF e Markdown, roteiro de apresentação e minuta de declaração de IA não assinada.

## Instalar e testar

Requer Python **3.11 ou superior**. A execução validada usou Python 3.12 no Windows. No PowerShell, dentro desta pasta:

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
~~~

requirements.txt contém as dependências de execução; requirements-dev.txt inclui pytest, pypdf e networkx para validação. **Networkx só aparece nos testes**, como oráculo; não é usado na lógica de produção.

## Reproduzir o projeto inteiro

~~~powershell
.\.venv\Scripts\python.exe -m src.cli --all
~~~

Esse comando recalcula os resultados, executa os benchmarks reais e gera as figuras, o HTML e os documentos. Bellman-Ford na rede completa é a parte mais demorada. Os tempos mudam conforme a máquina e a carga do sistema. Não há chamada a serviços de IA durante a execução.

Os resultados já estão incluídos em out/ e os documentos em docs/. Abra **out/parte1/labirinto_interativo.html** no navegador. A interface funciona sem servidor e sem internet.

## Site publicado

O labirinto está disponível em [GitHub Pages](https://artur-antunes-1.github.io/projeto-grafos-g1-5b-2026-2/).

O workflow .github/workflows/pages.yml publica apenas o HTML interativo como index.html, sem recalcular os experimentos. Atualizações desse HTML na branch main são publicadas automaticamente; a opção Run workflow permite republicar manualmente. Para atualizar os resultados do site, execute o projeto e envie o HTML regenerado ao repositório.

## Comandos individuais

~~~powershell
# Caminho no mapa; exportação de JSON e arestas
.\.venv\Scripts\python.exe -m src.cli --mapa data/mapas/m03_tres_chaves.txt --alg DIJKSTRA

# Bônus e pesos negativos
.\.venv\Scripts\python.exe -m src.cli --mapa data/mapas/m05_bonus.txt --alg BELLMAN_FORD

# Corrigir a fonte infinita
.\.venv\Scripts\python.exe -m src.cli --mapa data/mapas/m06_fonte.txt --alg BELLMAN_FORD --fonte-consumivel

# Armadilhas e interface de um mapa
.\.venv\Scripts\python.exe -m src.cli --mapa data/mapas/m04_esteiras.txt --armadilhas --interactive

# Custo transformado 10-rating no dataset
.\.venv\Scripts\python.exe -m src.cli --dataset data/dataset_parte2 --alg DIJKSTRA --source 1 --target 8

# Experimentos do dataset e regeneração dos documentos
.\.venv\Scripts\python.exe -m src.cli --dataset data/dataset_parte2 --benchmark
.\.venv\Scripts\python.exe -m src.cli --report
~~~

--out pasta define outra saída; com --all recebe parte1/ e parte2/. --no-render omite gráficos e PDF. --repeticoes N exige N >= 5. python -m src.solve oferece a mesma interface.

## Resultados principais da Parte 1

As contagens excluem ALVO e seus arcos; passos contam apenas movimentos físicos.

| Mapa | Estados | Arcos | BFS: passos / custo | Menor custo | Armadilhas |
| --- | ---: | ---: | --- | ---: | ---: |
| m01 | 24 | 46 | 10 / 30 | 20 | 0 |
| m02 | 39 | 74 | 34 / 46 | 46 | 0 |
| m03 | 213 | 466 | 87 / 119 | 99 | 0 |
| m04 | 37 | 66 | 20 / 36 | 36 | 4 |
| m05 | 215 | 438 | 12 / 18 | 5 | 0 |
| m06 | 24 | 46 | 10 / 10 | Sem mínimo finito | 0 |
| m06 consumível | 40 | 76 | 10 / 10 | 10 | 0 |
| m07 | 16 | 38 | Sem solução | Sem solução | 16 |
| m08 | 2.919 | 6.364 | 392 / 524 | 482 | 0 |
| G1 - três desvios | 84 | 160 | 38 / 39 | 39 | 0 |
| G1 - queda sem volta | 57 | 158 | 16 / 16 | 16 | 40 |

Dijkstra recusa m05, m06, m06 consumível e o primeiro mapa do G1 porque contêm pesos negativos. Os custos finitos desses casos são obtidos por Bellman-Ford. DFS mostra um percurso da árvore de busca, sem garantia de mínimo.

## Dataset e pergunta de pesquisa

**Como o alcance dirigido varia entre fontes, como se distribuem os sinais e quando existe um saldo mínimo finito de avaliações?**

O CSV recebido tem 24.185 avaliações e 3.782 usuários. Os bytes recebidos foram preservados, incluindo a ausência de um registro existente na [fonte SNAP](https://snap.stanford.edu/data/soc-sign-bitcoin-alpha.html). A diferença e os hashes estão em data/dataset_parte2/README.md e docs/PROVENIENCIA.json. Artur informou que o dataset foi aprovado pelas duas professoras; a proposta original aprovada ainda precisa ser anexada.

Bellman-Ford usa rating: minimizar a soma pode acumular desconfiança; não recomenda confiança transitiva. Dijkstra usa 10-rating, outro objetivo, não negativo. O controle sem ciclo é um recorte em DAG por camadas BFS, mantendo pesos e direção dos dados. O caso cíclico mostra dois arcos de soma -20, validados no CSV.

O desenho experimental, as séries de tempos, médias e análises estão em out/parte2/parte2_report.json, benchmarks.csv, case_benchmarks.csv, analise.md e notas_analiticas.md. As amostras de 10%, 50% e 100% têm, respectivamente, 378/332, 1.891/6.368 e 3.782/24.185 nós/arcos.

## Organização e documentos

src/graphs/ contém IO, grafo e algoritmos; parte1.py e parte2.py executam os experimentos; viz.py gera figuras/interface; report.py gera documentos. tests/ contém casos manuais, integração e oráculos independentes. As fontes originais estão em docs/referencias/.

- docs/RELATORIO_TECNICO.pdf e .md: manual, modelagem, provas, resultados e limitações.
- docs/ROTEIRO_APRESENTACAO.md: roteiro de 15 a 20 minutos.
- docs/REGISTRO_IA.md: registro da geração integral assistida.
- docs/CONTRIBUICOES.md: matriz sem atribuições humanas fictícias.
- docs/DECLARACAO_IA.pdf: minuta não assinada; não substitui o modelo oficial.
- docs/CHECKLIST.md: requisitos técnicos e pendências externas.

Entrega indicada: 26/11/2026, por todos os integrantes. Apresentação da turma 5B: 01/12/2026. Presença, domínio conceitual, contribuições efetivas, aprovação documentada e assinaturas dependem das pessoas do grupo e não são comprovados por este repositório.
