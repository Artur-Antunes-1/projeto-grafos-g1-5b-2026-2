# Notas analíticas das figuras — Parte 2 [IA]

Autoria assistida integralmente por IA. Estas notas explicam os resultados medidos, o desenho dos gráficos e seus limites.

## Variáveis e papéis

SOURCE e TARGET são identificadores nominais: o valor numérico do ID não mede importância, confiança ou ordem temporal. SOURCE é emissor da avaliação e TARGET é receptor. Graus de saída/entrada são contagens nesses papéis. RATING é uma escala discreta assinada definida pela plataforma; as somas e médias são uma convenção operacional deste experimento e não unidades psicológicas de confiança. TIME é temporal (segundos Unix); os meses são UTC. Os gráficos relacionam rating com mês e com contagens de emissão/recepção, preservando os papéis dirigidos.

## 1. Exploratória — distribuição dos ratings

Mostra a contagem em cada valor de -10 a 10, inclusive valores sem registros. Há 22649 avaliações positivas (93.65%), 1536 negativas e 0 zeros. Barras são adequadas à escala discreta e deixam frequências nulas visíveis. As três cores e a legenda identificam o sinal, e o eixo cobre a escala completa. A frequência dos sinais não autoriza concluir que a rede inteira é confiável.

## 2. Exploratória — relação entre emissão, recepção e negativas

Cada ponto combina grau de saída (emissor), grau de entrada (receptor) e cor para o número de negativas recebidas: três variáveis derivadas dos registros. O usuário 1 tem maior entrada (397); 7604 recebe 69 negativas em 73 avaliações. Dispersão permite procurar concentração, associação e casos fora da tendência; symlog acomoda zeros e uma faixa ampla. Os rótulos destacam maiores entradas, não IDs numericamente maiores. A barra de cores explicita as contagens de negativas. A cor é contagem absoluta, portanto também depende da exposição; não é taxa de risco e a relação não prova causalidade. Pontos sobrepostos podem ocultar usuários.

## 3. Exploratória — alcance e distância dirigida

As barras separam alcançáveis de inalcançáveis, e as linhas mostram quantos usuários surgem em cada camada. Resultados desta versão: fonte 1: 3748 alcançáveis, 34 inalcançáveis, profundidade máxima 5; fonte 8: 3748 alcançáveis, 34 inalcançáveis, profundidade máxima 5; fonte 1359: 3748 alcançáveis, 34 inalcançáveis, profundidade máxima 7. Barras com parte/todo e linhas em distâncias inteiras facilitam comparar volume e distribuição. As legendas distinguem os conjuntos e as fontes. Destaques são os vértices inalcançáveis e as camadas mais distantes de cada fonte, com contagens descritas acima. BFS ignora rating, e ausência de caminho não prova ausência de relação fora do arquivo.

## 4. Exploratória — rating e tempo de registro

A área empilhada separa volumes mensais positivos, negativos e zeros, expondo variação temporal de contagens e sinais. O pico total ocorre em 2011-06 com 2424 registros. A área evidencia composição e volume; meses ordenados permitem localizar o pico, sem usar ID como tempo. O destaque não identifica a causa, não conta usuários ativos e não acompanha a mudança de opinião de uma mesma pessoa. A categoria zero permanece identificada na legenda e tem 0 registros nesta versão.

## Da exploração à explicação

As explorações investigam a distribuição de sinais, a concentração de avaliações e o alcance dirigido da versão selecionada. As explicações seguintes isolam duas consequências verificáveis: transformar ratings muda o objetivo dos caminhos; conservar ciclos negativos pode eliminar o mínimo finito. Não se escolheu um caminho para recomendar confiança nem para movimentar bitcoins.

## 5. Explanatória — dois objetivos nos mesmos pares

Duas barras por par comparam BFS e Dijkstra em número de arcos e em soma de 10-rating, em painéis com as mesmas categorias. Dijkstra usa mais arcos em 9 dos 9 pares; obtém custo transformado estritamente menor em 9 e igual em 0. Barras agrupadas facilitam comparação par a par; os dois painéis mostram a relação observada entre número de arcos e custo. O destaque é que minimizar quantidade de arcos e custo transformado são objetivos distintos, mesmo quando os resultados coincidem. Como ∑(10-rating)=10k−∑rating, variar k impede tratar a transformação como equivalente ao mínimo original ou a confiança transitiva.

## 6. Explanatória — ciclo negativo e controle finito

O diagrama mostra o ciclo real 7565 → 7553 → 7565, com soma -20, e o painel contrasta seus 3748 usuários afetados com o controle DAG de 3748 nós/7261 arcos, que preserva 547 avaliações negativas. Um desenho local com setas, legenda e pesos permite conferir a direção e a soma sem esconder o ciclo no desenho da rede inteira; o texto distingue finito, inalcançável e sem mínimo. Repetir a soma negativa -20 reduz a soma ilimitadamente. O controle remove retornos entre camadas e não implica que a rede original seja acíclica; não há interpretação financeira.

## 7. Comparação dos algoritmos — tempo na rede completa

As barras mostram medianas das 5 execuções locais de cada tarefa. BF tem mediana 6.403614s, pois precisa detectar/propagar ciclos no modelo original; BFS/DFS/Dijkstra realizam tarefas distintas. A escala log permite visualizar ordens de grandeza sem ocultar tempos pequenos, os rótulos mostram segundos e a legenda identifica cada algoritmo/tarefa. O destaque é o custo medido do caso cíclico, não uma classificação universal de algoritmos. Médias, dispersão, fontes e tarefas constam das tabelas, impedindo confundir objetivos diferentes.

## 8. Escalabilidade — três subgrafos induzidos

As linhas usam medianas e barras de mínimo–máximo dos subgrafos induzidos com seed 42. Contagens reais por fração de nós (nós/arcos): 10%: 378/332; 50%: 1891/6368; 100%: 3782/24185. A fração de nós não fixa a fração de arcos, por isso ambas as contagens são informadas. Linhas evidenciam a mudança medida, e barras mostram a variação sem pressupor distribuição dos tempos. A escala log mantém as curvas legíveis, e a legenda identifica os algoritmos. Fontes e tarefas são documentadas; estes tamanhos, 5 repetições e carga de fundo não demonstram uma lei assintótica nem desempenho em outra máquina.

## Ausências, outliers e integridade

Foram observadas 0 células ausentes nos campos exigidos; há 0 pares repetidos e 0 laços. Zero campos ausentes não identifica o mecanismo de ausência, nem prova completude da rede. Outliers de grau e negativas são observações descritivas; não são erros descartados. CSV recebido reconhecido pelo SHA-256: 24185 registros/3782 usuários; SNAP original tem 24186/3783. A comparação desta cópia foi documentada; não foi reinserido o registro ausente. Nenhuma execução temporal foi removida como outlier.
