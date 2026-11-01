# Plano da implementação completa

Solicitação: desenvolver a versão completa do projeto G1/5B, com assistência de IA registrada sem atribuição fictícia a integrantes.

## Arquitetura e contratos

Python 3.11+. Núcleo próprio, sem bibliotecas de algoritmos em `src/`. `networkx` somente em `tests/`. IO separado da representação, dos algoritmos e das visualizações. Nenhuma assinatura ou contribuição humana será simulada. Dataset recebido preservado (24.185 registros).

- `DirectedGraph.adj`: dicionário de nó para lista ordenada de `Edge(target, weight, movement='', cell='')`. Nós hashable. `add_node`, `add_edge`, `edges()` produz `(u, v, peso)`, `transpose()`. `len(graph)` devolve ordem.
- `bfs(graph, source)`, `dfs(graph, source)`, `dijkstra(graph, source)` e `bellman_ford(graph, source)` devolvem dicionários. BFS: `distance`, `parent`, `order`. DFS: `parent`, `order`, `discover`, `finish`, `classification` (lista de `(u,v,tipo)`), `has_cycle`. Dijkstra/BF: `distance`, `parent`, `negative_cycle` (lista fechada, vazia quando ausente), `affected` (nós sem mínimo finito). Função `reconstruct_path(parent, source, target)`.
- `read_map(path)` devolve `Maze(name, rows, start, goals, keys, bonus_positions, source_positions)`. Coordenadas base zero; `rows` lista de strings. `parse_map(text, name='mapa')` para testes.
- `build_state_graph(maze, consumable_source=False)` devolve `(graph, initial_label, states)`. `states` é dict rótulo -> `State(row,col,keys:frozenset,bonus:frozenset)`. `State.label()` formato `(1,1)|-|{}`. ALVO está no grafo, fora de states. Fontes consumíveis ocupam índices após os bônus normais no conjunto `bonus`.
- `build_position_graph(maze, doors='floor')` devolve `(graph, start_tuple, goal_tuples)`. Não inclui ALVO. Respeita esteiras e termina em G. `doors='wall'` exclui portas; `'floor'` permite.
- `src/parte1.py`: `run_part1(root, out, render=True)` processa todos os mapas, exporta tabelas/JSON e chama `src/viz.py`.
- `src/parte2.py`: `run_part2(root, out, repetitions=5, render=True)` lê CSV, constrói modelos documentados, executa casos e benchmarks e exporta JSON/figuras/notas.
- `src/viz.py`: `render_part1(payload, out)` recebe dict por nome do mapa. Cada mapa: `rows`, `states` (rótulo -> `{row,col,keys,bonus}`), `edges` (lista `{source,target,weight,movement,cell}`), `solutions` (algoritmo -> `{status,path,cost,steps,trace}`), `traps` (rótulos), `metrics`. Trace: lista `{state,row,col,keys,bonus,cost}` sem ALVO. Gera PNGs e HTML autossuficiente, sem algoritmos em JS.

## Execução

1. Núcleo e testes: escrever casos pequenos verificáveis antes da implementação. Testar pesos negativos, ciclos alcançáveis/inalcançáveis, classificação DFS completa, mapas inválidos, bônus e chaves, transposto e ALVO.
2. Parte 1: criar dois mapas próprios, cumprir percurso com três chaves/bônus/esteira e proporção de armadilhas >=20%; gerar todos os arquivos e contagens. Testar métricas sem ALVO, custo/passos sem arco virtual, estados terminais.
3. Parte 2: pergunta sobre alcance, sinais e existência de saldo mínimo de avaliações. Pesos originais `rating` (mínimo acumula desconfiança, não recomenda confiança); versão Dijkstra `10-rating` (outra função objetivo, não equivalente). Caso BF sem ciclo por recorte em DAG, mantendo pesos dos dados; caso com ciclo na rede original. Fontes/pares determinísticos, cinco repetições medidas e subgrafos induzidos aninhados de 10%,50%,100% dos nós. Registrar nós/arestas reais e ambiente.
4. Visualização: mapas, camadas, árvore e heatmap; HTML com seleção/estado/custo/controle e armadilhas/camadas; quatro exploratórias e duas explanatórias do dataset, mais comparação de algoritmos e notas.
5. Integração: CLI para mapa/dataset, exportação completa, fonte consumível e modo interativo; teste de ponta a ponta, pytest, revisão independente e teste visual no navegador.
6. Documentação: README com comandos verificados, relatório técnico/manual em PDF e Markdown, roteiro de defesa, declaração de IA não assinada explicitando geração integral. Registrar limites de conformidade, contribuições e assinaturas pendentes.
7. Publicação: conferir resultados, hashes de fontes, ausência de secrets, criar commits reais de assistência de IA, integrar à main e verificar privacidade e ref remoto.

## Pontos de revisão

- G termina o jogo, exceto arco virtual de custo zero; ALVO não entra nas métricas do mapa nem em passos físicos.
- Distâncias de vértices afetados por ciclo negativo são menos infinito; ciclos desconectados da fonte não contaminam sua resposta.
- Bônus e chaves são memória monotônica; esteiras podem produzir estados sem saída.
- Grafo assinado não significa confiança transitiva; transformações mudam a pergunta.
- Tempos são medidos localmente; nenhum resultado ou contribuição será inventado.

## Registro de progresso

- Preparação: escopo técnico, contratos e limitações registrados antes da implementação.
- Núcleo e Parte 1: implementados e executados, com oráculos independentes; ALVO excluído das métricas e passos, armadilhas conferidas por transposto.
- Parte 2: três fontes, nove pares, controle DAG, ciclo negativo validado nos registros; cinco medições por tarefa e três tamanhos reais.
- Interface: controles, estados de erro, animação e camadas verificados no navegador; corrigido mínimo intrínseco do grid em telas estreitas; nenhuma requisição externa para executar a interface.
- Revisão: corrigidos status BF sem destino, cabeçalho CSV de mapa sem arcos e colisão de nomes entre fonte original/consumível, com regressões vermelhas e verdes.
- Documentação: relatório/manual, roteiro e minuta de declaração gerados; sem assinaturas ou atribuições humanas simuladas.
