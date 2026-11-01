# Entregas e pendências

Base: enunciado e critérios originais em `referencias/`. As caixas técnicas indicam artefatos gerados e verificados com assistência integral de IA; não comprovam autoria, participação ou domínio dos estudantes. As restrições acadêmicas de IA não foram cumpridas por esta versão.

## Preparação

- [x] Registrar G1, turma 5B, e os cinco integrantes.
- [x] Organizar os oito mapas e o CSV recebido.
- [x] Registrar a confirmação de Artur de que o dataset foi aprovado.
- [ ] Arquivar a proposta aprovada e o modelo oficial da declaração de IA.
- [ ] Definir donos e revisores dos cinco pacotes.
- [ ] Registrar a escolha da versão do dataset, considerando a diferença documentada.

## Parte 1

- [ ] Desenho à mão do grafo de estados do m02 antes de programar: não realizado/comprovado nesta produção assistida.
- [x] Implementar leitura/validação, grafo dirigido e construção por estados alcançáveis.
- [x] Respeitar a ordem N, L, S, O, custos de destino, chaves, portas, esteiras e bônus.
- [x] Implementar o ALVO virtual, com arcos de custo zero a partir das saídas; excluí-lo das métricas da seção 3 do enunciado.
- [x] Implementar BFS, DFS com classificação de arcos, Dijkstra com recusa de pesos negativos e Bellman-Ford com retorno do ciclo negativo.
- [x] Gerar `arestas_<mapa>.csv`, inclusive m08 e mapas do grupo.
- [x] Gerar `metricas_global.json`, `camadas.json` e `graus_<mapa>.csv`.
- [x] Calcular rankings de graus, multiplicidade e becos.
- [x] Gerar `comparacao_modelagem.csv` para m02, m03 e m04.
- [x] Gerar a prova do m05, identificada como assistência de IA.
- [x] Implementar e discutir a opção `--fonte-consumivel` para m06.
- [x] Demonstrar a ausência de solução do m07 pelo código do grupo.
- [x] Gerar `solucoes.csv`, `percurso_m03.json`, `ciclo_negativo_m06.json`, `dfs_classificacao.csv` e armadilhas de m04/m07.
- [x] Criar percurso de m03/m08 por camada de chaves, grafo em camadas e árvore BFS do m02 e heatmap de multiplicidade do m08.
- [x] Criar HTML interativo ou Streamlit com seleção, animação acompanhável, estado/custo, armadilhas e alternância de camadas.
- [x] Criar os dois mapas próprios e documentar seus gabaritos.
- [x] Garantir três chaves, esteiras e bônus no primeiro mapa próprio; o caminho mínimo deve usar bônus e esteira.
- [x] Garantir pelo menos 20% de estados-armadilha no segundo mapa próprio.

## Parte 2

- [x] Formular e justificar a pergunta de pesquisa e os significados dos pesos, caminhos e ciclos.
- [x] Explorar estrutura, distribuições, relações e outliers; justificar tratamentos de ausências e inconsistências.
- [x] Executar BFS e DFS de pelo menos três fontes.
- [x] Executar Dijkstra em pelo menos cinco pares, com transformação de pesos justificada pelo grupo.
- [x] Executar Bellman-Ford nos casos sem ciclo negativo e com ciclo negativo exibido.
- [x] Medir pelo menos cinco execuções por algoritmo/tarefa e pelo menos três tamanhos do grafo.
- [x] Gerar `out/parte2/parte2_report.json`.
- [x] Comparar algoritmos e desenvolver a discussão crítica gerada com IA.
- [x] Escolher e justificar as visualizações; produzir notas analíticas e interpretação geradas com IA.
- [x] Atender às seis visualizações do enunciado: quatro exploratórias e duas explanatórias, uma respondendo à pergunta.

Os slides mencionam quatro visualizações (duas exploratórias e duas explanatórias), enquanto o enunciado, p. 10, pede seis. Confirmar a exigência com as professoras; a lista acima adota a quantidade maior para planejamento.

## Testes e entrega

- [x] Testar BFS, DFS dirigida, Dijkstra e Bellman-Ford nos casos mínimos exigidos.
- [x] Testar estados em mapa de até 5x7 com contagens manuais, esteira sem saída e mudança de camada por chave.
- [x] Testar mapas inválidos e mensagens de erro.
- [x] Atualizar README com comandos reais de execução e teste.
- [x] Produzir PDF manual/técnico com resultados, limitações, conclusões e matriz de contribuição.
- [ ] Preparar reflexão autoral de 10 a 15 linhas sobre o uso de IA.
- [ ] Preencher o modelo oficial e obter as cinco assinaturas em `docs/DECLARACAO_IA.pdf`.
- [x] Conferir os registros de apoio de IA e marcações `# [IA]` pertinentes.
- [ ] Registrar contribuições reais de todos em pelo menos dois pacotes.
- [ ] Preparar apresentação de 15 a 20 minutos e execução ao vivo de mapa surpresa.
- [ ] Todos os integrantes postarem o material em 26/11/2026.

## Validação técnica

A suíte contém testes manuais, de integração e oráculos NetworkX restritos a tests/. A interface foi testada no navegador em 1440px e 390px, com animação, camadas, armadilhas e controles offline. CSVs e JSONs foram conferidos contra os resultados dos algoritmos. Os hashes dos materiais recebidos permanecem os mesmos.

A implementação técnica não substitui as etapas humanas pendentes acima. Os PDFs e textos descrevem explicitamente a assistência integral e a minuta não assinada.
