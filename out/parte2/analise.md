# Parte 2 — alcance, sinais e saldo de avaliações

## Pergunta e modelos

Como o alcance dirigido varia entre fontes, como se distribuem os sinais e quando existe um saldo mínimo finito de avaliações?

BFS/DFS ignoram os ratings e investigam alcance/estrutura. Bellman-Ford minimiza a soma dos ratings originais: procurar valores menores acumula desconfiança e não mede confiança transitiva. Dijkstra usa 10-rating em cada arco, com custos de 0 a 20; isto penaliza avaliações menores e cobra 10 por arco. Os objetivos são diferentes e não são comparados como se fossem equivalentes.

## Evidências medidas

- O arquivo preservado contém 24185 avaliações dirigidas e 3782 usuários; SHA-256 d2f121d67f325ba2dfbbf0e9708843d7c9b0f898494957fb6b1b239db5150c8a.
- Há 22649 avaliações positivas (93.65%), 1536 negativas e 0 zeros. Média 1.464; mediana 1.
- A densidade dirigida sem laços é 0.001691. 83.21% dos arcos têm o arco reverso; isto não indica concordância de ratings.
- O usuário 1 recebe 397 avaliações, maior grau de entrada observado. Há 28 usuários sem entrada e 497 sem saída.
- O usuário 7604 recebe 69 avaliações negativas entre 73 recebidas, com média -8.603; é o maior número absoluto de negativas recebidas, não uma prova sobre sua identidade ou conduta.
- Alcance BFS por fonte: 1: 3748 alcançáveis, 34 inalcançáveis, profundidade máxima 5; 8: 3748 alcançáveis, 34 inalcançáveis, profundidade máxima 5; 1359: 3748 alcançáveis, 34 inalcançáveis, profundidade máxima 7.
- Nos 9 pares alcançáveis, Dijkstra escolheu caminho diferente de BFS em 9; usou mais arcos em 9. Em todos, o custo transformado de Dijkstra é menor ou igual ao do caminho BFS.
- O controle em DAG conserva 3748 nós/7261 arcos, incluindo 547 negativos. Da fonte 1, o menor saldo finito é -20 até 7363.
- Na rede original, BF da fonte 2 encontra ciclo [7565, 7553, 7565] de soma -20; 3748 vértices não têm mínimo finito. Repetir o ciclo permite somas arbitrariamente negativas.
- Ausências: {'SOURCE': 0, 'TARGET': 0, 'RATING': 0, 'TIME': 0}; pares dirigidos repetidos: 0; laços: 0. Zero ausências observadas não determina mecanismo de ausência nem completude social.

## Desenho experimental

As 3 fontes são escolhidas de forma determinística: maior grau de saída; maior número de avaliações negativas emitidas; e posição mediana entre usuários com saída. Empates usam ID e duplicações são substituídas pelo próximo maior grau. Para cada fonte, escolhem-se destinos nas posições 25%, 65% e 100% da ordenação (distância BFS, ID), sem repetir destinos.

O controle de Bellman-Ford mantém apenas vértices alcançáveis e arcos reais que avançam estritamente nas camadas BFS. Os pesos e direções permanecem originais; o aumento estrito da camada prova ausência de ciclos. Este controle altera a rede e não autoriza conclusões de aciclicidade sobre a rede original.

Benchmarks: 5 execuções por algoritmo/tarefa em 10%, 50% e 100% dos nós. Embaralhamento dos IDs ordenados com random.Random(42); prefixos aninhados e todas as arestas induzidas, incluindo nós isolados. A fonte de BFS/DFS/Dijkstra é a de maior saída em cada subgrafo. BF prefere o menor ID participante de ciclo recíproco negativo; se não existir, usa maior saída. As fontes constam no CSV. O tempo usa perf_counter, inclui criação do resultado e detecção/propagação dos ciclos, e exclui leitura, construção dos modelos e renderização. Não há remoção de outliers temporais, aquecimento descartado ou timeout escondido.

| Nós selecionados | Nós reais | Arcos reais | Algoritmo | Fonte | Média (s) | Mediana (s) | Mínimo–máximo (s) |
|---|---:|---:|---|---:|---:|---:|---:|
| 10% | 378 | 332 | BFS | 1 | 0.0000584 | 0.0000559 | 0.0000520–0.0000692 |
| 10% | 378 | 332 | DFS | 1 | 0.0001193 | 0.0001141 | 0.0001070–0.0001335 |
| 10% | 378 | 332 | Dijkstra | 1 | 0.0001399 | 0.0001331 | 0.0001304–0.0001641 |
| 10% | 378 | 332 | Bellman-Ford | 145 | 0.0103500 | 0.0104354 | 0.0098667–0.0105519 |
| 50% | 1891 | 6368 | BFS | 1 | 0.0017114 | 0.0017678 | 0.0015786–0.0018204 |
| 50% | 1891 | 6368 | DFS | 1 | 0.0041761 | 0.0043088 | 0.0028372–0.0050286 |
| 50% | 1891 | 6368 | Dijkstra | 1 | 0.0043353 | 0.0043360 | 0.0035188–0.0050818 |
| 50% | 1891 | 6368 | Bellman-Ford | 6 | 1.1290843 | 0.9459579 | 0.8008474–1.6242668 |
| 100% | 3782 | 24185 | BFS | 1 | 0.0019619 | 0.0018789 | 0.0017327–0.0023469 |
| 100% | 3782 | 24185 | DFS | 1 | 0.0059182 | 0.0058656 | 0.0051438–0.0072145 |
| 100% | 3782 | 24185 | Dijkstra | 1 | 0.0063034 | 0.0058712 | 0.0054376–0.0075448 |
| 100% | 3782 | 24185 | Bellman-Ford | 2 | 6.4059060 | 6.4036144 | 6.0013967–6.7620213 |

## 5 medições por caso obrigatório

Além da escala, BFS/DFS são medidos separadamente por fonte; Dijkstra por par, incluindo a busca completa da fonte e reconstrução do destino; BF no controle DAG. O caso BF original reutiliza as 5 medições da mesma fonte e tarefa em 100%, sem contá-las como novas amostras. Séries individuais e origem estão em case_benchmarks.csv e no JSON.

| Algoritmo | Fonte | Destino | Caso | Média (s) | Mediana (s) |
|---|---:|---:|---|---:|---:|
| BFS | 1 | — | alcance original por fonte | 0.0019190 | 0.0018418 |
| DFS | 1 | — | travessia/classificação original por fonte | 0.0053782 | 0.0052862 |
| BFS | 8 | — | alcance original por fonte | 0.0018624 | 0.0018546 |
| DFS | 8 | — | travessia/classificação original por fonte | 0.0051339 | 0.0051177 |
| BFS | 1359 | — | alcance original por fonte | 0.0017936 | 0.0017912 |
| DFS | 1359 | — | travessia/classificação original por fonte | 0.0050693 | 0.0050548 |
| Dijkstra | 1 | 638 | 10-rating; busca completa da fonte e reconstrução do par | 0.0052083 | 0.0052119 |
| Dijkstra | 1 | 1656 | 10-rating; busca completa da fonte e reconstrução do par | 0.0055408 | 0.0053328 |
| Dijkstra | 1 | 7450 | 10-rating; busca completa da fonte e reconstrução do par | 0.0055183 | 0.0054678 |
| Dijkstra | 8 | 1219 | 10-rating; busca completa da fonte e reconstrução do par | 0.0061185 | 0.0060806 |
| Dijkstra | 8 | 1973 | 10-rating; busca completa da fonte e reconstrução do par | 0.0059159 | 0.0056522 |
| Dijkstra | 8 | 7450 | 10-rating; busca completa da fonte e reconstrução do par | 0.0056469 | 0.0051701 |
| Dijkstra | 1359 | 1021 | 10-rating; busca completa da fonte e reconstrução do par | 0.0052695 | 0.0051137 |
| Dijkstra | 1359 | 674 | 10-rating; busca completa da fonte e reconstrução do par | 0.0055030 | 0.0054617 |
| Dijkstra | 1359 | 2666 | 10-rating; busca completa da fonte e reconstrução do par | 0.0054556 | 0.0055876 |
| Bellman-Ford | 1 | 7363 | controle DAG com ratings negativos reais | 0.0049821 | 0.0046141 |
| Bellman-Ford | 2 | — | rede original; detecção/propagação de ciclo negativo | 6.4059060 | 6.4036144 |

## Comparação de ordens e estrutura

BFS organiza vértices por distância mínima em arcos; DFS aprofunda cada ramo antes de retornar. A ordem depende da ordem dos arcos do arquivo preservado e não constitui um ranking dos usuários. Ambos alcançam o mesmo conjunto por fonte. Arcos de retorno na DFS testemunham ciclos dirigidos, mas não determinam o sinal total de um ciclo.

- Fonte 1: primeiros 12 em BFS: [1, 160, 1028, 309, 11, 594, 1316, 1392, 1583, 888, 637, 1520]; em DFS: [1, 160, 18, 11, 2, 37, 4, 302, 60, 14, 9, 20]. Classificações DFS: {'arvore': 3747, 'retorno': 11267, 'cruzamento': 362, 'avanco': 8764}; ciclo alcançável: True.
- Fonte 8: primeiros 12 em BFS: [8, 2, 3, 5, 6, 7, 521, 600, 396, 306, 25, 7380]; em DFS: [8, 2, 1, 160, 18, 11, 3, 5, 67, 4, 302, 60]. Classificações DFS: {'arvore': 3747, 'retorno': 11250, 'cruzamento': 366, 'avanco': 8777}; ciclo alcançável: True.
- Fonte 1359: primeiros 12 em BFS: [1359, 3, 42, 5, 92, 6, 207, 123, 287, 103, 34, 56]; em DFS: [1359, 3, 5, 2, 1, 160, 18, 11, 4, 302, 60, 14]. Classificações DFS: {'arvore': 3747, 'retorno': 11264, 'cruzamento': 367, 'avanco': 8762}; ciclo alcançável: True.

## Ambiente e limites

Python 3.12.14; Windows-11-10.0.26300-SP0; processador Intel64 Family 6 Model 170 Stepping 4, GenuineIntel. Medição local, sem controle de carga de fundo. Tempos não são previsão de desempenho em outra máquina e três tamanhos não demonstram limites assintóticos.

CSV recebido reconhecido pelo SHA-256: 24185 registros/3782 usuários; SNAP original tem 24186/3783. A comparação desta cópia foi documentada; não foi reinserido o registro ausente. O experimento usa somente os bytes do arquivo selecionado. A rede deve ser interpretada no contexto da versão e da plataforma documentadas. Concentração, correlação, ausência de caminho e distribuição de sinais não estabelecem causalidade, identidade, recomendação de confiança, nem representatividade de outras plataformas. Não há inferência de mecanismo de dados ausentes a partir de zero campos vazios.

Toda implementação, seleção operacional dos casos, análise e figuras desta entrega receberam assistência integral de IA. Autoria e contribuições humanas não são simuladas.

## Figuras

- [exploratoria_01_ratings.png](exploratoria_01_ratings.png): Distribuição de todos os ratings do CSV recebido, incluindo frequências zero na escala. Cores indicam sinal, não probabilidade de confiança.
- [exploratoria_02_graus.png](exploratoria_02_graus.png): Cada ponto é um usuário. Escala symlog mantém zeros. Rótulos identificam os três maiores graus de entrada; sobreposição pode esconder pontos.
- [exploratoria_03_alcance.png](exploratoria_03_alcance.png): BFS ignora rating. A fonte conta na camada zero. Ausência de caminho dirigido não implica ausência de relação social fora dos registros.
- [exploratoria_04_tempo.png](exploratoria_04_tempo.png): Agregação mensal UTC dos registros disponíveis. Não estima usuários ativos, causalidade ou evolução de confiança individual.
- [explanatoria_01_objetivos.png](explanatoria_01_objetivos.png): Comparação nos mesmos pares. BFS minimiza arcos; Dijkstra minimiza ∑(10-rating). O termo 10 é cobrado a cada arco: não equivale a maximizar a soma de ratings quando o número de arcos varia.
- [explanatoria_02_ciclo.png](explanatoria_02_ciclo.png): O ciclo foi validado arco a arco no CSV recebido. O controle retira arcos que não avançam nas camadas BFS; não descreve a rede original como acíclica.
- [comparacao_algoritmos.png](comparacao_algoritmos.png): Tempos do mesmo ambiente, excluindo leitura/construção/figuras. Tarefas e pesos diferem: BFS/DFS alcance, Dijkstra custo transformado, BF saldo original e ciclos; não é ranking de algoritmos equivalentes.
- [benchmark_tempos.png](benchmark_tempos.png): Amostra uniforme de nós, mantendo inclusive isolados e todas as arestas induzidas. Contagens reais e tempos individuais estão no JSON/CSV. Três tamanhos não provam complexidade assintótica.

## Referência

Stanford SNAP, Bitcoin Alpha: https://snap.stanford.edu/data/soc-sign-bitcoin-alpha.html. Kumar et al., Edge Weight Prediction in Weighted Signed Networks, IEEE ICDM, 2016.
