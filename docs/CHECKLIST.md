# Entregas e pendências

Base: enunciado e critérios originais em `referencias/`. Esta lista organiza os requisitos; não representa resultados já obtidos.

## Preparação

- [x] Registrar G1, turma 5B, e os cinco integrantes.
- [x] Organizar os oito mapas e o CSV recebido.
- [x] Registrar a confirmação de Artur de que o dataset foi aprovado.
- [ ] Arquivar a proposta aprovada e o modelo oficial da declaração de IA.
- [ ] Definir donos e revisores dos cinco pacotes.
- [ ] Registrar a escolha da versão do dataset, considerando a diferença documentada.

## Parte 1

- [ ] Desenhar à mão o grafo de estados do m02 antes de programar.
- [ ] Implementar leitura/validação, grafo dirigido e construção por estados alcançáveis.
- [ ] Respeitar a ordem N, L, S, O, custos de destino, chaves, portas, esteiras e bônus.
- [ ] Implementar o ALVO virtual, com arcos de custo zero a partir das saídas; excluí-lo das métricas da seção 3 do enunciado.
- [ ] Implementar BFS, DFS com classificação de arcos, Dijkstra com recusa de pesos negativos e Bellman-Ford com retorno do ciclo negativo.
- [ ] Gerar `arestas_<mapa>.csv`, inclusive m08 e mapas do grupo.
- [ ] Gerar `metricas_global.json`, `camadas.json` e `graus_<mapa>.csv`.
- [ ] Calcular rankings de graus, multiplicidade e becos.
- [ ] Gerar `comparacao_modelagem.csv` para m02, m03 e m04.
- [ ] Desenvolver a prova autoral do m05.
- [ ] Implementar e discutir a opção `--fonte-consumivel` para m06.
- [ ] Demonstrar a ausência de solução do m07 pelo código do grupo.
- [ ] Gerar `solucoes.csv`, `percurso_m03.json`, `ciclo_negativo_m06.json`, `dfs_classificacao.csv` e armadilhas de m04/m07.
- [ ] Criar percurso de m03/m08 por camada de chaves, grafo em camadas e árvore BFS do m02 e heatmap de multiplicidade do m08.
- [ ] Criar HTML interativo ou Streamlit com seleção, animação acompanhável, estado/custo, armadilhas e alternância de camadas.
- [ ] Criar os dois mapas próprios e documentar seus gabaritos.
- [ ] Garantir três chaves, esteiras e bônus no primeiro mapa próprio; o caminho mínimo deve usar bônus e esteira.
- [ ] Garantir pelo menos 20% de estados-armadilha no segundo mapa próprio.

## Parte 2

- [ ] Formular e justificar a pergunta de pesquisa e os significados dos pesos, caminhos e ciclos.
- [ ] Explorar estrutura, distribuições, relações e outliers; justificar tratamentos de ausências e inconsistências.
- [ ] Executar BFS e DFS de pelo menos três fontes.
- [ ] Executar Dijkstra em pelo menos cinco pares, com transformação de pesos justificada pelo grupo.
- [ ] Executar Bellman-Ford nos casos sem ciclo negativo e com ciclo negativo exibido.
- [ ] Medir pelo menos cinco execuções por algoritmo/tarefa e pelo menos três tamanhos do grafo.
- [ ] Gerar `out/parte2/parte2_report.json`.
- [ ] Comparar algoritmos e desenvolver a discussão crítica autoral.
- [ ] Escolher e justificar as visualizações; produzir notas analíticas e interpretação autorais.
- [ ] Atender às seis visualizações do enunciado: quatro exploratórias e duas explanatórias, uma respondendo à pergunta.

Os slides mencionam quatro visualizações (duas exploratórias e duas explanatórias), enquanto o enunciado, p. 10, pede seis. Confirmar a exigência com as professoras; a lista acima adota a quantidade maior para planejamento.

## Testes e entrega

- [ ] Testar BFS, DFS dirigida, Dijkstra e Bellman-Ford nos casos mínimos exigidos.
- [ ] Testar estados em mapa de até 5x7 com contagens manuais, esteira sem saída e mudança de camada por chave.
- [ ] Testar mapas inválidos e mensagens de erro.
- [ ] Atualizar README com comandos reais de execução e teste.
- [ ] Produzir PDF manual/técnico com resultados, limitações, conclusões e matriz de contribuição.
- [ ] Preparar reflexão autoral de 10 a 15 linhas sobre o uso de IA.
- [ ] Preencher o modelo oficial e obter as cinco assinaturas em `docs/DECLARACAO_IA.pdf`.
- [ ] Conferir os registros de apoio de IA e marcações `# [IA]` pertinentes.
- [ ] Registrar contribuições reais de todos em pelo menos dois pacotes.
- [ ] Preparar apresentação de 15 a 20 minutos e execução ao vivo de mapa surpresa.
- [ ] Todos os integrantes postarem o material em 26/11/2026.
