# Roteiro de apresentação e estudo - G1 / 5B

Material integralmente gerado com assistência de IA (OpenAI Codex), incluindo código, mapas, soluções, demonstrações, análise, seleção das visualizações e texto. O enunciado proíbe vários desses usos. Este documento não demonstra conformidade acadêmica nem comprova participação, domínio ou autoria humana dos integrantes.

Este roteiro foi gerado por IA. Não é relato de estudo, participação ou domínio dos integrantes. A divisão abaixo é por assunto; nenhum apresentador humano foi atribuído.

## Preparação real antes da defesa

Ler o código e os resultados; conferir os exemplos à mão; executar os comandos do README; explicar os caminhos sem decorar o texto; pedir orientação às docentes sobre os usos proibidos de IA. Não afirmar que houve essa preparação sem realizá-la.

## Sequência sugerida: 18 minutos

| Tempo | Tema | Demonstração |
|---|---|---|
| 0-1 min | Objetivo e transparência | Informar produção integral com IA e limites acadêmicos. |
| 1-4 min | Estado, direção e ALVO | Desenhar o mapa mínimo: 7 estados/10 arcos físicos; 8/11 com ALVO. |
| 4-7 min | Algoritmos nos labirintos | m01: BFS 10/30 e Dijkstra 14/20; m05 bônus consumível; m06 ciclo e correção. |
| 7-9 min | Camadas, armadilhas e mapas G1 | m02 com/sem chave; m07 com 16 estados e nenhuma saída; 40/57 armadilhas no G1-02. |
| 9-12 min | Dataset e pergunta | Preservar 24185/3782; distinguir rating e 10-rating; 3 fontes. |
| 12-15 min | Figuras e resposta | Predominância positiva, ciclo -20 real e controle DAG com 547 negativos. |
| 15-17 min | Desempenho e limites | Médias de 5 execuções, três tamanhos e tarefas diferentes. |
| 17-18 min | Execução de mapa e fechamento | Rodar TXT surpresa com --mapa e explicar o estado/custo/status. |

## Comandos de demonstração

```powershell
python -m src.cli --mapa data/mapas/m01_terreno.txt --alg BFS --out out/demo
python -m src.cli --mapa data/mapas/m01_terreno.txt --alg DIJKSTRA --out out/demo
python -m src.cli --mapa data/mapas/m05_bonus.txt --alg BELLMAN_FORD --out out/demo
python -m src.cli --mapa data/mapas/m06_fonte.txt --alg BELLMAN_FORD --out out/demo
python -m src.cli --mapa data/mapas/m06_fonte.txt --alg BELLMAN_FORD --fonte-consumivel --out out/demo_corrigida
python -m src.cli --mapa data/mapas/m07_impossivel.txt --armadilhas --out out/demo
python -m src.cli --dataset data/dataset_parte2 --alg DIJKSTRA --source 1 --target 638 --out out/demo_dataset
```

Abrir out/parte1/labirinto_interativo.html. Avançar manualmente pelo percurso, trocar a camada e destacar armadilhas. Não narrar um status de recusa ou ciclo como se fosse um ótimo finito.

## Perguntas para conferir entendimento individual

1. Por que duas visitas à mesma casa podem ser nós diferentes?
2. Por que não há estado sem chave na casa a do mapa mínimo?
3. Por que G tem arco para ALVO, mas nenhum movimento físico de saída?
4. Por que BFS usa mais custo em m01 mesmo com menos passos?
5. Por que o consumo monotônico de bônus elimina ciclos negativos no m05?
6. Por que fonte consumível ainda leva Dijkstra a recusar o grafo?
7. Como o transposto distingue armadilha de beco?
8. Por que minimizar 10-rating não equivale a minimizar rating?
9. Como a camada estritamente crescente prova que o controle é DAG?
10. Qual evidência valida o ciclo 7565→7553→7565 e quais destinos ele afeta?
11. O que foi medido nos tempos, o que ficou fora e por que as tarefas não são equivalentes?
12. Que informações não são autorizadas pelos dados (causalidade, identidade, confiança transitiva)?

## Materiais a consultar

docs/RELATORIO_TECNICO.pdf e .md; out/parte1/resultados.json; out/parte2/parte2_report.json; CSV de tempos individuais; notas analíticas e figuras em out/parte2/. A declaração é minuta não assinada. A participação individual permanece não comprovada.
