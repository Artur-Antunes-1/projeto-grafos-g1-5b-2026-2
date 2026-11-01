# [IA] OpenAI Codex - geração integral do relatório, manual, declaração e roteiro.
"""Documentação derivada dos resultados existentes, sem executar algoritmos.

Use ``python -m src.cli --report`` depois de gerar ``out/parte1`` e
``out/parte2``. A declaração é uma minuta não assinada, não o modelo oficial.
"""
from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image, KeepTogether, PageBreak, Paragraph, Preformatted,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)


MEMBERS = ['Artur Antunes', 'Ricardo Machado', 'Victor Uen', 'Luca Ribeiro', 'Pedro Ferraz']
NOTICE = (
    'Material integralmente gerado com assistência de IA (OpenAI Codex), incluindo '
    'código, mapas, soluções, demonstrações, análise, seleção das visualizações e texto. '
    'O enunciado proíbe vários desses usos. Este documento não demonstra conformidade '
    'acadêmica nem comprova participação, domínio ou autoria humana dos integrantes.'
)


def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _num(value, digits=4):
    if value is None:
        return '-'
    if isinstance(value, int):
        return str(value)
    return f'{value:.{digits}f}'


def _short(name):
    if name == 'm06_fonte_consumivel':
        return 'm06 consumível'
    return name.split('_')[0] if name.startswith('m') else name.replace('g1_0', 'G1-0').split('_')[0]


def _font():
    candidates = [
        (Path('C:/Windows/Fonts/arial.ttf'), Path('C:/Windows/Fonts/arialbd.ttf')),
        (Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
         Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')),
    ]
    for regular, bold in candidates:
        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont('ReportBody', str(regular)))
            pdfmetrics.registerFont(TTFont('ReportBold', str(bold)))
            pdfmetrics.registerFontFamily('ReportBody', normal='ReportBody', bold='ReportBold')
            return
    raise OSError('Instale Arial ou DejaVu Sans para gerar PDFs com caracteres portugueses.')


def _styles():
    _font()
    base = getSampleStyleSheet()
    styles = {}
    for key, size, leading in [('body', 9.5, 13.4), ('small', 8.3, 11.2), ('table', 7.6, 10.1), ('caption', 8.5, 11.5)]:
        styles[key] = ParagraphStyle(key, fontName='ReportBody', fontSize=size, leading=leading,
                                     textColor=colors.HexColor('#20252c'), spaceAfter=7)
    styles['title'] = ParagraphStyle('title', parent=base['Title'], fontName='ReportBold', fontSize=23,
                                     leading=29, alignment=TA_LEFT, spaceAfter=18, textColor=colors.HexColor('#183b50'))
    styles['heading'] = ParagraphStyle('heading', fontName='ReportBold', fontSize=16, leading=20,
                                       spaceAfter=13, textColor=colors.HexColor('#183b50'))
    styles['sub'] = ParagraphStyle('sub', fontName='ReportBold', fontSize=11.3, leading=15,
                                   spaceBefore=6, spaceAfter=7, textColor=colors.HexColor('#183b50'))
    styles['notice'] = ParagraphStyle('notice', parent=styles['small'], borderColor=colors.HexColor('#b86621'),
                                      borderWidth=.6, borderPadding=9, backColor=colors.HexColor('#fff5e9'), spaceAfter=16)
    styles['code'] = ParagraphStyle('code', fontName='Courier', fontSize=8, leading=10.5, spaceAfter=9)
    return styles


class Report:
    def __init__(self, title):
        self.title, self.pages, self.current = title, [], None

    def page(self, title):
        self.current = [('heading', title)]
        self.pages.append(self.current)

    def p(self, text, style='body'):
        self.current.append(('p', text, style))

    def sub(self, title):
        self.current.append(('sub', title))

    def code(self, text):
        self.current.append(('code', text))

    def table(self, headers, rows, widths=None):
        self.current.append(('table', headers, rows, widths))

    def image(self, path, caption, max_height=350):
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f'Figura necessária ao relatório: {path}')
        self.current.append(('image', path, caption, max_height))

    def markdown(self, destination):
        destination = Path(destination)
        lines = [f'# {self.title}', '']
        for page in self.pages:
            for item in page:
                kind = item[0]
                if kind == 'heading':
                    lines += [f'## {item[1]}', '']
                elif kind == 'sub':
                    lines += [f'### {item[1]}', '']
                elif kind == 'p':
                    lines += [item[1], '']
                elif kind == 'code':
                    lines += ['```text', item[1], '```', '']
                elif kind == 'table':
                    def cell(value):
                        return str(value).replace('|', '\\|').replace('\n', '<br>')
                    lines.append('| ' + ' | '.join(map(cell, item[1])) + ' |')
                    lines.append('| ' + ' | '.join(['---'] * len(item[1])) + ' |')
                    lines += ['| ' + ' | '.join(map(cell, row)) + ' |' for row in item[2]]
                    lines.append('')
                elif kind == 'image':
                    target = os.path.relpath(item[1], destination.parent).replace('\\', '/')
                    lines += [f'![{item[2]}]({target})', '', item[2], '']
        destination.write_text('\n'.join(lines), encoding='utf-8')

    def pdf(self, destination, *, declaration=False):
        styles = _styles()
        width = A4[0] - 88
        story = []

        def para(text, style='body'):
            safe = escape(str(text)).replace('\n', '<br/>')
            return Paragraph(safe, styles[style])

        for index, page in enumerate(self.pages):
            if index:
                story.append(PageBreak())
            for item in page:
                kind = item[0]
                if kind in ('heading', 'sub'):
                    story.append(para(item[1], 'title' if not index and kind == 'heading' else kind))
                elif kind == 'p':
                    story.append(para(item[1], item[2]))
                elif kind == 'code':
                    story.append(Preformatted(item[1], styles['code']))
                elif kind == 'table':
                    headers, rows, proportions = item[1:]
                    proportions = proportions or [1] * len(headers)
                    total = sum(proportions)
                    cells = [[para(cell, 'table') for cell in row] for row in [headers] + list(rows)]
                    table = Table(cells, colWidths=[width * p / total for p in proportions], repeatRows=1, hAlign='LEFT')
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e3edf2')),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f8f9')]),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('LINEBELOW', (0, 0), (-1, 0), .6, colors.HexColor('#97aebc')),
                        ('LINEBELOW', (0, 1), (-1, -1), .2, colors.HexColor('#dbe1e5')),
                    ]))
                    story.extend([table, Spacer(1, 9)])
                elif kind == 'image':
                    path, caption, height_limit = item[1:]
                    w, h = ImageReader(str(path)).getSize()
                    scale = min(width / w, height_limit / h)
                    story.append(KeepTogether([Image(str(path), width=w * scale, height=h * scale, hAlign='CENTER'),
                                                Spacer(1, 5), para(caption, 'caption')]))
        def decorate(canvas, document):
            canvas.saveState()
            canvas.setFont('ReportBody', 7)
            canvas.setFillColor(colors.HexColor('#61717b'))
            label = 'MINUTA NÃO ASSINADA - USO INTEGRAL DE IA' if declaration else 'G1 / 5B - Relatório técnico e manual - geração integral com IA'
            canvas.drawString(44, A4[1] - 27, label)
            canvas.setStrokeColor(colors.HexColor('#d5dfe4'))
            canvas.line(44, 36, A4[0] - 44, 36)
            canvas.drawString(44, 24, 'Resultados locais reproduzíveis; autoria humana e conformidade não comprovadas.')
            canvas.drawRightString(A4[0] - 44, 24, str(document.page))
            canvas.restoreState()
        document = SimpleDocTemplate(str(destination), pagesize=A4, rightMargin=44, leftMargin=44,
                                     topMargin=49, bottomMargin=48, title=self.title,
                                     author='OpenAI Codex - geração integral com IA', subject='G1 / turma 5B',
                                     invariant=1)
        document.build(story, onFirstPage=decorate, onLaterPages=decorate)


def _notes(path):
    text = Path(path).read_text(encoding='utf-8')
    notes = {}
    for match in re.finditer(r'^## ([1-8])\. ([^\n]+)\n(.*?)(?=^## |\Z)', text, re.M | re.S):
        notes[int(match[1])] = ' '.join(match[3].split())
    if len(notes) != 8:
        raise ValueError('notas_analiticas.md deve conter as oito notas numeradas de 1 a 8.')
    return notes


def _report(root, out):
    p1dir, p2dir = out / 'parte1', out / 'parte2'
    p1 = _read(p1dir / 'resultados.json')
    metrics = _read(p1dir / 'metricas_global.json')
    layers = _read(p1dir / 'camadas.json')
    group = _read(p1dir / 'gabarito_mapas_grupo.json')
    bonus = _read(p1dir / 'comparacao_bonus_m05.json')
    cycle = _read(p1dir / 'ciclo_negativo_m06.json')
    fix = _read(p1dir / 'fonte_consumivel_m06.json')
    p2 = _read(p2dir / 'parte2_report.json')
    notes = _notes(p2dir / 'notas_analiticas.md')
    # A análise é insumo explícito; os números são lidos do JSON, sem cópia manual.
    analysis_text = (p2dir / 'analise.md').read_text(encoding='utf-8')
    if not analysis_text.strip():
        raise ValueError('A análise da Parte 2 está vazia.')
    with (p1dir / 'comparacao_modelagem.csv').open(encoding='utf-8-sig', newline='') as stream:
        comparisons = list(csv.DictReader(stream))
    report = Report('Labirintos com chaves e redes de avaliações')
    r = report

    r.page('Labirintos com chaves e redes de avaliações')
    r.p('Teoria dos Grafos e Análise e Visualização de Dados - 2026.2\nGrupo G1 - Turma 5B', 'sub')
    r.p('Integrantes informados: ' + '; '.join(MEMBERS) + '.')
    r.p(NOTICE, 'notice')
    r.sub('Resumo')
    r.p('A Parte 1 representa labirintos como grafos dirigidos de estados e compara alcance, número de passos e custo. A Parte 2 aplica os mesmos quatro algoritmos ao arquivo recebido da rede Bitcoin Alpha, preservando sua versão. Os resultados diferenciam três respostas: caminho finito, destino inalcançável e inexistência de mínimo por ciclo negativo.')
    r.p(f'Foram processados dez mapas e uma variante de regra. Na Parte 2, foram preservados {p2["dataset"]["rows"]} registros e {p2["dataset"]["nodes"]} usuários; os tempos são medições locais com {p2["repetitions"]} repetições por tarefa.')
    r.sub('Como ler')
    r.p('O manual vem primeiro. Em seguida estão a modelagem, as tabelas dos mapas, as cinco figuras da Parte 1, os experimentos e as oito figuras da Parte 2. A seção final responde à pergunta de pesquisa e registra limites e participação não comprovada.')
    r.sub('Situação acadêmica')
    r.p('Artur informou que o dataset foi aprovado. Essa informação não equivale a comprovante documental de aprovação. A produção integral com IA excede os usos permitidos pelo enunciado. A declaração anexa é apenas uma minuta não assinada e não substitui o modelo da professora. Este material requer revisão humana real e decisão das docentes antes de qualquer uso como entrega.')

    r.page('1. Manual de execução')
    r.p('Requisito: Python 3.11 ou superior. Execute os comandos na raiz do repositório. A implementação usa lista de adjacência própria; heapq auxilia Dijkstra. Bibliotecas prontas de algoritmos não participam da execução de src/.')
    r.code('python -m venv .venv\n.venv\\Scripts\\Activate.ps1\npython -m pip install -r requirements-dev.txt\npython -m pytest -q\npython -m src.cli --all --repeticoes 5')
    r.p('A execução completa gera as duas partes, imagens, CSV/JSON, HTML interativo e os documentos em docs/. Benchmarks têm custo local variável, sobretudo Bellman-Ford. --no-render permite produzir apenas os dados; --report regenera os documentos de resultados já existentes.')
    r.code('python -m src.cli --report\npython -m src.cli --all --no-render --repeticoes 5')
    r.sub('Consultas e comparação de regras')
    r.code('python -m src.cli --mapa data/mapas/m03_tres_chaves.txt \\\n  --alg DIJKSTRA --out out/consulta\npython -m src.cli --mapa data/mapas/m06_fonte.txt \\\n  --alg BELLMAN_FORD --fonte-consumivel --out out/fonte\npython -m src.cli --mapa data/mapas/m04_esteiras.txt \\\n  --armadilhas --interactive --out out/consulta\npython -m src.cli --dataset data/dataset_parte2 --alg DIJKSTRA \\\n  --source 1 --target 638 --out out/consulta_dataset')
    r.p('As barras invertidas no fim das linhas acima indicam continuação visual: no PowerShell, digite cada comando em uma linha, ou use o acento grave como continuação. O README contém exemplos em uma linha.')
    r.sub('Usar a apresentação interativa')
    r.p('Abra out/parte1/labirinto_interativo.html no navegador. Escolha mapa e algoritmo, inicie ou avance manualmente, ajuste a velocidade e acompanhe posição, chaves, bônus e custo. Use o filtro de camada e a marcação de armadilhas. Casos RECUSA, CICLO_NEGATIVO e SEM_SOLUCAO são resultados e não devem aparecer como percurso de menor custo válido.')
    r.p('Um mapa surpresa pode ser salvo como TXT e passado a --mapa. Linhas de comentário começam com ponto e vírgula. Erros de grade, símbolos, número de inícios ou ausência de saída encerram a consulta com mensagem.')

    r.page('2. Representação do labirinto')
    r.p('G_pos contém uma casa livre por vértice. G_est contém estados (linha, coluna, K, B): K é o conjunto de chaves adquiridas; B identifica os bônus consumidos. Coordenadas começam em zero. O rótulo (1,1)|a|{0} indica chave a e bônus 0 já coletado. A mesma posição em dois conjuntos K/B corresponde a vértices diferentes.')
    r.table(['Símbolo', 'Regra e custo de entrada'], [
        ['#', 'Parede; sem vértice transitável.'], ['. / S / G', 'Custo 1; S é único; G encerra o jogo.'],
        [', / ~', 'Lama custa 3; água custa 5.'], ['a..d / A..D', 'Chave custa 1 e permanece; porta custa 1 e exige a chave correspondente.'],
        ['> < ^ v', 'Entrada custa 1; a saída do estado só segue a seta.'], ['+', 'Primeira entrada custa -4; seguintes custam 1, registrando consumo em B.'],
        ['*', 'Regra original: -2 em toda entrada. Variante: -2 uma vez e 1 depois.'],
    ], [1, 5])
    r.p('A construção explora apenas estados alcançáveis a partir de S e testa vizinhos em N, L, S, O. O custo pertence à casa de destino. Depois de entrar em uma chave ou bônus, atualiza a memória antes de identificar o novo estado. Não são pré-geradas todas as combinações possíveis.')
    r.sub('Direção, término e nó virtual')
    r.p('Esteiras impedem o retorno por um arco espelhado; coletar uma chave ou um bônus também muda a memória sem operação inversa. Um grafo não dirigido criaria movimentos que o jogo não permite. G não tem movimentos físicos de saída. De cada estado em G sai somente um arco virtual de custo zero para ALVO.')
    r.p('Os algoritmos buscam ALVO. Ordem, tamanho, densidade e graus do mapa excluem ALVO e seus arcos. A contagem de passos físicos também exclui o arco final. Como todo percurso de sucesso inclui exatamente um arco virtual, BFS preserva a escolha por menor quantidade de movimentos físicos.')
    r.p('O teto é F × 2^k × 2^b, sendo F casas livres, k chaves e b bônus. A variante consumível conta fontes como itens de memória. A ocupação é |V_est|/teto; a densidade dirigida é |E|/[|V|(|V|-1)], ou zero quando |V|<2.')

    r.page('3. Um mapa mínimo conferido à mão')
    r.code('#######\n#S.aAG#\n#######')
    r.p('A grade tem 3 × 7, dentro do limite 5 × 7. As únicas posições livres são (1,1) a (1,5). Não há bônus. Inicialmente K é vazio. É possível ficar nas colunas 1 e 2 sem chave; entrar na coluna 3 coleta a. Portanto não existe estado na coluna 3 sem a, e a porta da coluna 4 é inacessível sem a.')
    r.table(['Memória', 'Estados físicos alcançáveis', 'Quantidade'], [
        ['K vazio', '(1,1)|-|{} e (1,2)|-|{}', '2'],
        ['K={a}', 'Colunas 1, 2, 3, 4 e 5 da linha 1, todas com a', '5'],
        ['Total', '2 + 5', '7'],
    ], [1, 4, 1])
    r.sub('Enumeração dos dez arcos físicos')
    r.p('Sem chave há 1→2 e 2→1, além de 2→3 com mudança de memória: 3 arcos. Com a há 1↔2, 2↔3, 3↔4 e 4→5: 7 arcos. Não existe 5→4, pois a coluna 5 é G e o jogo terminou. O arco 2→3 sem a e o arco 2→3 com a saem de estados diferentes.')
    r.table(['Convenção', 'Vértices', 'Arcos'], [
        ['Somente estados e movimentos físicos', '7', '10'],
        ['Incluindo ALVO e G→ALVO', '8', '11'],
    ], [4, 1, 1])
    r.p('O caminho BFS é S(1) → chão(2) → a(3) → A(4) → G(5) → ALVO. São quatro movimentos físicos, custo 1+1+1+1=4. A distância BFS até ALVO é cinco arcos, mas o relatório exporta quatro passos físicos.')
    r.p('Essa contagem é independente do programa e funciona como caso de verificação: o teste deve confirmar 7 estados físicos/10 arcos, ou 8 nós/11 arcos com ALVO. Também deve confirmar que a coleta altera a camada e que uma esteira direcionada à parede não ganha saída artificial.')
    r.p('O mapa mínimo serve para validar a representação. Ele não substitui os dois mapas próprios do grupo, que têm requisitos adicionais.')

    r.page('4. Métricas globais de todos os cenários')
    r.p('Cada linha usa as definições da seção 2. G_pos trata portas como chão para permitir a comparação geométrica; os movimentos de esteira e o término em G permanecem. Os dez mapas recebidos/criados são acompanhados pela variante de m06.')
    rows = []
    for name, m in metrics.items():
        rows.append([_short(name), m['G_pos']['order'], m['G_pos']['size'], _num(m['G_pos']['density'], 5),
                     m['G_est']['order'], m['G_est']['size'], _num(m['G_est']['density'], 5),
                     m['theoretical_ceiling'], _num(m['occupancy'] * 100, 2) + '%'])
    r.table(['Mapa', 'V pos', 'E pos', 'D pos', 'V est', 'E est', 'D est', 'Teto', 'Ocup.'], rows,
            [1.7, 1, 1, 1.3, 1, 1, 1.3, 1.2, 1.2])
    r.p('m06 consumível é uma execução do mesmo mapa com a regra corrigida. Os demais rótulos m01 a m08 correspondem aos arquivos fornecidos; G1-01 e G1-02 aos mapas em data/mapas_grupo/. Todas as métricas da tabela excluem ALVO.')
    m8 = metrics['m08_grande']
    r.p(f'Em m08, só {m8["G_est"]["order"]} dos {m8["theoretical_ceiling"]} estados do teto são alcançáveis ({m8["occupancy"]:.2%}). Portas restringem a ordem das chaves e o término elimina extensões depois de G. O teto não prevê que cada subconjunto de chaves exista em cada casa.')
    r.p('A densidade menor de G_est não significa menor dificuldade: o denominador cresce com o quadrado da ordem. Em m07, a exploração descarta casas geometricamente livres que não podem ser alcançadas com as regras do inventário.')
    r.sub('Proveniência e conferência')
    r.p('Fontes: metricas_global.json e resultados.json. As arestas completas estão em arestas_<mapa>.csv e os graus físicos em graus_<mapa>.csv. A variante corrigida também está detalhada em fonte_consumivel_m06.json; não é um décimo primeiro arquivo de mapa independente.')

    r.page('5. Graus, multiplicidade e becos')
    rows = []
    for name, m in metrics.items():
        rows.append([_short(name), str(m['max_indegree']) + '\n' + m['max_indegree_state'],
                     str(m['max_outdegree']) + '\n' + m['max_outdegree_state'],
                     m['max_multiplicity'], len(m['max_multiplicity_cells']), len(m['dead_ends'])])
    r.table(['Mapa', 'Maior entrada: grau / estado', 'Maior saída: grau / estado', 'M máx.', 'Casas em M máx.', 'Becos'], rows,
            [1.4, 3, 3, .75, 1, .75])
    r.p('O desempate dos rankings é lexicográfico pelo rótulo completo do estado. Grau de entrada conta arcos que chegam; saída conta arcos que partem. A ordem N, L, S, O organiza a exploração, mas não muda essa regra de desempate.')
    r.p(f'Multiplicidade é o número de estados físicos associados à mesma casa. Em m08 o máximo é {m8["max_multiplicity"]}, atingido por {len(m8["max_multiplicity_cells"])} casas. As camadas alcançáveis são {", ".join(layers["m08_grande"]["layers"])} (- significa vazio). Essas casas podem ser revisitadas com memórias distintas. Nem todos os subconjuntos teóricos são realizáveis, pois a coleta tem ordem restrita.')
    r.p('Beco é um estado fora de G com grau físico de saída zero. Um estado-armadilha pode ter saídas e até ciclos internos, mas nenhuma rota até ALVO. Por isso a quantidade de becos não é a quantidade de armadilhas.')
    for name, m in metrics.items():
        if m['dead_ends']:
            r.p(f'Becos de {_short(name)}: ' + '; '.join(m['dead_ends']) + '.', 'small')

    r.page('6. Camadas e mudanças de inventário')
    rows = []
    for name, item in layers.items():
        for key, layer in item['layers'].items():
            rows.append([_short(name), key, layer['order'], layer['size'], _num(layer['density'], 5)])
    r.table(['Mapa', 'Chaves', 'V na camada', 'E internos', 'Densidade'], rows, [1.6, 1, 1.3, 1.3, 1.4])
    r.p(f'Cada camada é um subgrafo induzido pelo mesmo conjunto de chaves. Bônus distintos permanecem dentro da camada de chaves e ainda podem separar estados. Por isso m05 tem uma única camada de chaves e {metrics["m05_bonus"]["G_est"]["order"]} estados físicos. Os tamanhos internos não incluem os arcos entre camadas.')
    crossings = []
    for name, item in layers.items():
        if item['crossings']:
            crossings.append(_short(name) + ': ' + '; '.join(f'{x["from"]}→{x["to"]} em ({x["row"]},{x["col"]}), {x["count"]} arco(s)' for x in item['crossings']))
    r.p('Mudanças de camada: ' + ' | '.join(crossings) + '.', 'small')
    r.p('Somente entrar em uma chave ainda ausente de K muda a camada. Portas apenas consultam K; terreno e esteira não o alteram. A mesma chave pode gerar mais de um arco entre camadas quando alcançada por estados predecessores diferentes.', 'small')

    r.page('7. Por que posições não bastam; prova do m05')
    r.table(['Mapa', 'Modelagem', 'Passos BFS', 'Válido?', 'Observação'], [
        [_short(x['mapa']), x['abordagem'].replace('_', ' '), x['passos'] or '-', 'sim' if x['caminho_valido'] == 'True' else 'não', x['observacao']]
        for x in comparisons], [1, 2.1, .8, .8, 2.9])
    r.p('Portas como chão permitem cruzar A/B/C antes da coleta e produzem atalhos inválidos. Portas como parede bloqueiam para sempre uma passagem que deveria abrir após obter a chave. G_est conserva a memória e permite revisitar a casa em outra situação. Os caminhos completos e a validação movimento a movimento constam no CSV.')
    r.sub('Bônus como peso fixo cria um ciclo falso')
    r.p(f'No G_pos de m05, tratar + como -4 em todas as entradas produz o ciclo {bonus["G_pos_cycle"]}, de custo {bonus["G_pos_cycle_cost"]}. O retorno pode cobrar +1 e a nova entrada no bônus -4; repetir rende -3 a cada volta. Isso não corresponde à regra consumível.')
    r.sub('Argumento de ausência de ciclo negativo em G_est')
    r.p('Ao longo de qualquer percurso, os conjuntos K e B apenas crescem por inclusão. Em um ciclo que retorna ao mesmo estado, K e B finais precisam ser iguais aos iniciais. Logo nenhum arco desse ciclo pode consumir um bônus novo ou adquirir uma chave nova. Toda entrada em + ao longo do ciclo já está consumida e custa 1. No m05 não há fonte permanente *; os demais custos físicos são positivos. Assim todo ciclo físico custa estritamente mais que zero. ALVO não tem saída e não participa de ciclo. Portanto G_est do m05 não tem ciclo negativo.')
    sol5 = p1['m05_bonus']['solutions']['BELLMAN_FORD']
    r.p(f'Bellman-Ford no G_est confirma ausência de ciclo negativo e encontra custo {sol5["cost"]} em {sol5["steps"]} passos. O argumento de monotonicidade explica o resultado; a execução sozinha não substitui a prova. Esta prova também foi gerada por IA e é um dos usos proibidos pelo enunciado.')

    r.page('8. Resultados de caminhos nos dez mapas e variante')
    def compact(solution):
        if solution['status'] != 'OK':
            return {'RECUSA': 'RECUSA', 'SEM_SOLUCAO': 'SEM SOLUÇÃO', 'CICLO_NEGATIVO': 'CICLO NEGATIVO'}[solution['status']]
        return f'{solution["steps"]} / {solution["cost"]}'
    r.table(['Mapa', 'BFS\npassos / custo', 'DFS\npassos / custo', 'Dijkstra\npassos / custo', 'Bellman-Ford\npassos / custo'],
            [[_short(name)] + [compact(item['solutions'][alg]) for alg in ['BFS', 'DFS', 'DIJKSTRA', 'BELLMAN_FORD']] for name, item in p1.items()], [1.5, 1.25, 1.25, 1.6, 1.6])
    r.p('Status exportados: OK, RECUSA, CICLO_NEGATIVO e SEM_SOLUCAO. Custo e passos ausentes não são zero. A tabela resume resultados de solucoes.csv/resultados.json; o arquivo de soluções contém os caminhos completos dos dez mapas. A variante de regra está em fonte_consumivel_m06.json.')
    r.sub('m01: minimizar passos ou custo')
    s1 = p1['m01_terreno']['solutions']
    r.p(f'BFS escolhe {s1["BFS"]["steps"]} passos, com custo {s1["BFS"]["cost"]}; Dijkstra escolhe {s1["DIJKSTRA"]["steps"]} passos e custo {s1["DIJKSTRA"]["cost"]}. BFS trata cada movimento como uma unidade e não distingue lama/água. O caminho mais longo pode evitar terreno caro. DFS fornece um percurso de visita dependente da ordem, sem garantia de ótimo de passos ou custo.')
    r.sub('Algoritmo e hipótese')
    r.p('BFS resolve número mínimo de arcos em O(V+E). DFS verifica alcance, estrutura e ciclos em O(V+E). Dijkstra com heap resolve custo sob pesos não negativos, em O((V+E) log V). A implementação recusa qualquer arco negativo, inclusive se distante da fonte. Bellman-Ford permite pesos negativos, custa O(VE) no pior caso e identifica vértices afetados por ciclos negativos alcançáveis.')
    r.p('Um ciclo negativo em região inalcançável não altera o problema de uma fonte. Também não basta existir ciclo alcançável: para retirar o mínimo de um destino, o ciclo precisa poder atingir esse destino. O estado de ALVO é verificado antes de declarar o labirinto sem mínimo finito.')

    r.page('9. DFS, armadilhas e correção da fonte')
    r.table(['Mapa', 'Árvore', 'Retorno', 'Avanço', 'Cruzamento', 'Armadilhas'],
            [[_short(name)] + [item['dfs_counts'].get(k, 0) for k in ['arvore', 'retorno', 'avanco', 'cruzamento']] + [len(item['traps'])] for name, item in p1.items()], [1.6, 1, 1, 1, 1.2, 1.1])
    r.p('Classificação usa tempos de descoberta/término em grafo dirigido: árvore descobre vértice; retorno aponta para ancestral ativo; avanço liga descendente já encerrado; cruzamento liga ramos. A classificação inclui os arcos virtuais até ALVO, ao contrário das métricas físicas. Um arco de retorno comprova ciclo alcançável, mas não seu sinal.')
    r.sub('Busca reversa e impossibilidade')
    r.p(f'Uma BFS em ALVO no transposto identifica todos os estados que podem alcançar uma saída. A diferença entre estados físicos alcançáveis e esse conjunto é a lista de armadilhas. m04 tem {len(p1["m04_esteiras"]["traps"])} armadilhas. m07 alcança {metrics["m07_impossivel"]["G_est"]["order"]} estados físicos e nenhum estado em G: ALVO não é alcançado; os {len(p1["m07_impossivel"]["traps"])} estados são armadilhas. Isso demonstra ausência de solução na busca completa do espaço alcançável.')
    r.sub('m06: exploit e alteração implementada')
    r.p(f'O ciclo real é {" → ".join(cycle["cycle"])}, custo {cycle["cost"]}. Voltar repetidamente à fonte reduz o custo sem limite e depois ainda é possível chegar a G. Na opção --fonte-consumivel, registra-se em B cada fonte já usada: primeira entrada -2, demais 1. O ciclo anterior deixa de retornar ao mesmo estado na primeira coleta e depois passa a ser positivo.')
    r.p(f'A variante tem {fix["metrics"]["G_est"]["order"]} estados e {fix["metrics"]["G_est"]["size"]} arcos físicos. Bellman-Ford retorna OK, {fix["solution"]["steps"]} passos, custo {fix["solution"]["cost"]}, sem ciclo negativo. Dijkstra ainda recusa, pois permanecem arcos de primeira coleta com peso -2. Corrigir a regra não transforma todo peso em não negativo.')

    r.page('10. Mapas próprios e gabaritos do G1')
    r.p('Os dois mapas abaixo foram produzidos com IA. A denominação mapas do grupo descreve o diretório e o escopo do exercício; não atribui criação humana aos integrantes. Os resultados são os de gabarito_mapas_grupo.json.')
    for name in group:
        r.sub(name + '.txt')
        r.code('\n'.join(p1[name]['rows']))
        g = group[name]
        r.p(f'{g["states"]} estados físicos; {g["arcs_without_ALVO"]} arcos físicos; {g["arcs_with_ALVO"]} arcos com ALVO; BFS {g["BFS"]} passos; custo mínimo {g["minimum_cost"]}; armadilhas {g["traps_fraction"]:.2%}.')
    r.p('G1-01 exige as chaves a, b e c para atravessar A, B e C. O menor custo registrado coleta ao menos um bônus e percorre a esteira >; a validação de geração verifica esses símbolos no trace de Bellman-Ford. O bônus torna Dijkstra inaplicável mesmo que o caminho ótimo tenha custo final positivo.')
    g2 = group['g1_02_queda_sem_volta']
    r.p(f'G1-02 contém uma queda por esteira v para a região inferior. A esteira bloqueia o retorno, mas deixa vários movimentos internos nessa região: são {metrics["g1_02_queda_sem_volta"]["traps_count"]} armadilhas em {g2["states"]} estados ({g2["traps_fraction"]:.2%}), acima do mínimo de 20%. O corredor superior ainda permite solução de {g2["BFS"]} passos e custo {g2["minimum_cost"]}.')

    r.page('11. Percurso de menor custo no m03')
    r.image(p1dir / 'percurso_m03.png', 'Figura 1. Caminho de menor custo no m03. A cor muda conforme o inventário; chaves impõem a sequência a, b, c. Fonte: resultados.json e percurso_m03.json.', 405)
    r.p('A visualização desenha a grade, os símbolos e a sequência do trajeto. Repetir a mesma casa depois da coleta não é redundância: a posição pode representar outro vértice em G_est. A porta liberada explica a necessidade de retornar por corredores já visitados.')
    s3 = p1['m03_tres_chaves']['solutions']
    r.p(f'O menor custo é {s3["BELLMAN_FORD"]["cost"]} em {s3["BELLMAN_FORD"]["steps"]} passos. O caminho BFS tem {s3["BFS"]["steps"]} passos e custo {s3["BFS"]["cost"]}. Assim, a exigência de chaves e os custos de terreno são decisões distintas: primeiro se modelam os movimentos permitidos; depois se escolhe qual função minimizar.')
    r.p('Limite visual: trechos que passam pela mesma casa podem se sobrepor. A conferência estado a estado deve usar percurso_m03.json ou o HTML interativo, que explicita chaves, consumo e custo acumulado.')

    r.page('12. Percurso de menor custo no m08')
    r.image(p1dir / 'percurso_m08.png', 'Figura 2. Percurso no mapa m08 (31 × 71), com quatro chaves. A legenda identifica as fases do inventário. Fonte: percurso_m08.json.', 385)
    s8 = p1['m08_grande']['solutions']
    r.p(f'O caminho de menor custo tem {s8["BELLMAN_FORD"]["steps"]} passos e custo {s8["BELLMAN_FORD"]["cost"]}. BFS encontra {s8["BFS"]["steps"]} passos e custo {s8["BFS"]["cost"]}. A exploração alcança {len(layers["m08_grande"]["layers"])} camadas, somando {m8["G_est"]["order"]} estados físicos e {m8["G_est"]["size"]} arcos físicos.')
    r.p(f'Este mapa mostra por que a geração por exploração evita combinações artificiais: embora existam {m8["G_pos"]["order"]} casas livres, só {m8["occupancy"]:.2%} do teto teórico é alcançável. A maior parte das combinações de inventário não existe nas posições dadas pelas portas.')
    r.p('A figura preserva o percurso geral. Para ampliar símbolos e consultar cada visita, abra o PNG original ou o HTML offline. A lista completa de transições é gerada no CSV de arestas; a sequência ótima é registrada no JSON.')

    r.page('13. Camadas do grafo de estados do m02')
    r.image(p1dir / 'camadas_m02.png', 'Figura 3. Camadas por inventário de chaves no m02; o arco destacado muda do conjunto vazio para {a}. Fonte: camadas.json e resultados.json.', 280)
    m2layers = layers['m02_uma_chave']['layers']
    r.p(f'A camada sem a tem {m2layers["-"]["order"]} estados e {m2layers["-"]["size"]} arcos internos. A camada com a tem {m2layers["a"]["order"]} estados e {m2layers["a"]["size"]} arcos internos. A coleta da chave liga as camadas e completa os {metrics["m02_uma_chave"]["G_est"]["size"]} arcos físicos.')
    r.p('O jogador não volta à camada vazia, pois chaves não são gastas. Pode, porém, retornar à posição inicial com a e atravessar a porta. Esse retorno espacial é um novo estado e não uma restauração do inventário antigo.')
    r.p('O desenho separa os conjuntos de chaves para mostrar a mudança de regra de acesso. A mesma chave já presente não abre uma terceira camada. Os graus e densidades são calculados no subgrafo induzido de cada camada, sem o arco de ligação.')

    r.page('14. Árvore BFS de estados do m02')
    r.image(p1dir / 'arvore_bfs_m02.png', 'Figura 4. Árvore BFS do m02 com níveis. Cada ligação é um predecessor de primeira descoberta; não representa todos os arcos do grafo.', 510)
    r.p(f'A árvore organiza estados por distância em arcos a partir do início. O caminho até G tem {p1["m02_uma_chave"]["solutions"]["BFS"]["steps"]} movimentos físicos; ALVO adiciona um arco virtual. Estados da mesma posição em inventários diferentes permanecem com rótulos diferentes. Arcos fora da árvore continuam presentes no CSV, mas são omitidos para preservar legibilidade.')

    r.page('15. Heatmap da multiplicidade no m08')
    r.image(p1dir / 'heatmap_m08.png', 'Figura 5. Multiplicidade de estados por casa no m08. A escala de cor conta visitas possíveis com memórias distintas, não frequência de uso por jogadores.', 350)
    r.p(f'O máximo de {m8["max_multiplicity"]} estados ocorre em {len(m8["max_multiplicity_cells"])} casas. Essas posições são alcançáveis antes e depois das quatro coletas sucessivas. A cor torna visível onde a mesma geometria se repete em mais camadas.')
    r.p('A multiplicidade é calculada contando os rótulos físicos por par (linha,coluna), incluindo todas as memórias alcançáveis; ALVO não pertence à grade. Não é uma estimativa probabilística de permanência nem de número de passagens no caminho ótimo.')
    r.sub('O que a Parte 1 permite concluir')
    r.p('A geometria sozinha não resolve o exercício. Inventário monotônico impede falsos ciclos de bônus, enquanto fontes permanentes podem gerar ciclos realmente negativos. BFS, Dijkstra e Bellman-Ford respondem a perguntas diferentes e DFS descreve a estrutura de exploração. Término em G, movimentos dirigidos e o tratamento de ALVO são necessários para manter contagens e respostas coerentes.')

    ds, structure = p2['dataset'], p2['structure']
    r.page('16. Parte 2: fonte, pergunta e qualidade')
    r.p('Pergunta: como o alcance dirigido varia entre fontes, como se distribuem os sinais das avaliações e em quais modelos existe um saldo mínimo finito? O domínio é a rede histórica de avaliações Bitcoin Alpha, disponibilizada pelo Stanford SNAP.')
    r.p('Fonte: ' + ds['source_url'] + '. Artigo de referência: Kumar et al., Edge Weight Prediction in Weighted Signed Networks, IEEE ICDM, 2016. A aprovação do uso foi informada por Artur; não foi fornecida a aprovação formal neste material.')
    r.table(['Aspecto', 'Resultado ou significado'], [
        ['Arquivo e versão', ds['file'] + '. ' + ds['version_note']],
        ['Tipo / dimensão', f'Dirigido, ponderado: {ds["nodes"]} nós e {ds["rows"]} arcos.'],
        ['Campos', 'SOURCE emissor; TARGET receptor; RATING avaliação discreta de -10 a +10; TIME segundos Unix.'],
        ['Intervalo UTC', ds['time_min_utc'] + ' a ' + ds['time_max_utc']],
        ['Sinais', f'{ds["sign_counts"]["positive"]} positivos; {ds["sign_counts"]["negative"]} negativos; {ds["sign_counts"]["zero"]} zeros.'],
        ['Rating', f'Mínimo {ds["rating_min"]}; máximo {ds["rating_max"]}; média {ds["rating_mean"]:.4f}; mediana {ds["rating_median"]}.'],
        ['Integridade', f'Ausências por campo: {ds["missing_by_column"]}; pares repetidos {ds["duplicate_directed_pairs"]}; laços {ds["self_loops"]}.'],
        ['Estrutura', f'Densidade {structure["density_without_loops"]:.6f}; {structure["reciprocal_arc_fraction"]:.2%} dos arcos têm reverso.'],
    ], [1.3, 5])
    r.p('SHA-256 do CSV recebido: ' + ds['sha256'], 'small')
    r.p(ds['version_note'] + ' Zero células vazias não prova completude social ou mecanismo de ausência. IDs são categorias nominais; a ordem numérica não mede importância. Ratings são ordinais da plataforma; somá-los é uma convenção operacional, sem unidade psicológica garantida.')
    r.p('Os quatro pilares são cobertos por estrutura/tipos e integridade; distribuição dos ratings e graus; relações entre emissão, recepção, negativas e tempo; e identificação de outliers sem exclusão automática. Relações observadas não demonstram causalidade. Os valores extremos de grau e avaliações foram mantidos como dados, e não tratados como erros por serem extremos.')

    r.page('17. Travessias a partir de três fontes')
    r.p('Escolha determinística: maior grau de saída; maior quantidade de negativas emitidas; posição mediana entre usuários com saída. Empates usam ID e duplicações são substituídas pelo próximo maior grau. O critério produz fontes ' + ', '.join(str(t['source']) for t in p2['traversals']) + '. BFS/DFS usam direções originais e ignoram os pesos.')
    r.table(['Fonte', 'Alcançáveis', 'Inalcançáveis', 'Profundidade', 'DFS: árvore / retorno / avanço / cruzamento'], [
        [t['source'], t['reachable'], t['unreachable'], t['max_distance'],
         ' / '.join(str(t['dfs']['classification_counts'].get(k, 0)) for k in ['arvore', 'retorno', 'avanco', 'cruzamento'])]
        for t in p2['traversals']], [1, 1, 1.1, 1, 3.5])
    r.table(['Fonte', 'Quantidade por camada BFS (da camada zero em diante)'], [
        [t['source'], '; '.join(f'{k}: {v}' for k, v in t['bfs']['layer_counts'].items())] for t in p2['traversals']], [1, 6])
    r.sub('Ordens de descoberta: primeiros doze')
    for t in p2['traversals']:
        r.p(f'Fonte {t["source"]}: BFS {t["bfs"]["order"][:12]}; DFS {t["dfs"]["order"][:12]}.', 'small')
    r.p('As ordens completas, pais, tempos DFS, classificações e camadas estão em parte2_report.json. A ordem respeita a sequência de arcos do arquivo recebido. BFS visita por menor distância em arcos; DFS aprofunda ramos. Nenhuma ordem é ranking de reputação.')
    r.p('Resultados por fonte: ' + '; '.join(f'{t["source"]} alcança {t["reachable"]}, profundidade {t["max_distance"]}, ciclo DFS {"sim" if t["dfs"]["has_cycle"] else "não"}' for t in p2['traversals']) + '. As distâncias e ordens diferem. Arcos de retorno testemunham ciclos alcançáveis, mas o sinal do ciclo exige os pesos e não pode ser inferido somente por DFS.')
    r.p('A ausência de caminho dirigido registrada na tabela é relativa à fonte e ao arquivo. Ela não prova ausência de relação social, de perfil ativo ou de vínculo fora dos registros.')

    acyclic = p2['bellman_ford_cases']['acyclic_control']
    nc = p2['bellman_ford_cases']['original_negative_cycle']
    r.page('18. Pesos, pares e casos de Bellman-Ford')
    r.p('Modelo original: peso = RATING. Minimizar sua soma procura valores mais negativos e acumula desconfiança; não é recomendação de confiança. Para Dijkstra, custo = 10-RATING, entre 0 e 20. Para um percurso com k arcos, soma(10-rating)=10k-soma(rating). O termo por arco muda o objetivo quando k varia; a transformação não preserva mínimos originais.')
    r.p(f'Para cada fonte, destinos foram selecionados nas posições 25%, 65% e 100% da ordenação (distância BFS, ID), sem repetição. São {len(p2["dijkstra_cases"])} pares, acima dos cinco exigidos. As buscas Dijkstra percorrem a fonte completa e depois reconstroem o destino.')
    r.table(['Par', 'Arcos BFS', 'Arcos Dijk.', 'Custo 10-r do BFS', 'Custo 10-r Dijk.', 'Soma rating Dijk.'], [
        [f'{x["source"]}→{x["target"]}', x['bfs_steps'], x['dijkstra_steps'], x['bfs_path_cost_10_minus_rating'],
         x['dijkstra_cost_10_minus_rating'], x['dijkstra_path_original_rating_sum']] for x in p2['dijkstra_cases']], [1.6, 1, 1, 1.3, 1.3, 1.4])
    more_arcs = sum(x['dijkstra_steps'] > x['bfs_steps'] for x in p2['dijkstra_cases'])
    lower_cost = sum(x['dijkstra_cost_10_minus_rating'] < x['bfs_path_cost_10_minus_rating'] for x in p2['dijkstra_cases'])
    example = p2['dijkstra_cases'][0]
    r.p(f'Dijkstra usa mais arcos em {more_arcs} pares e custo transformado estritamente menor em {lower_cost}. Por exemplo, {example["source"]}→{example["target"]} passa por {example["dijkstra_path"]}, custo {example["dijkstra_cost_10_minus_rating"]}, enquanto BFS usa {example["bfs_path"]}, custo {example["bfs_path_cost_10_minus_rating"]}. Isso compara objetivos explicitados, não corretude de algoritmos para uma mesma função de custo.')
    r.sub('Controle com negativos e mínimo finito')
    r.p(f'O controle mantém somente arcos reais que avançam estritamente de camada BFS: {acyclic["nodes"]} nós, {acyclic["edges"]} arcos, {acyclic["negative_edges"]} negativos; {acyclic["removed_edges"]} arcos retirados. A camada inteira cresce em cada arco e não pode retornar ao início de um ciclo. Bellman-Ford da fonte {acyclic["source"]} encontra {acyclic["path"]}, custo {acyclic["cost"]}, sem ciclo negativo. O recorte muda a rede; não resolve os mínimos da rede original.')
    r.sub('Caso original com ciclo negativo')
    r.p(f'Da fonte {nc["source"]}, BF encontra {nc["negative_cycle"]}, custo {nc["cycle_cost"]}. Cada arco foi conferido no CSV: ' + '; '.join(f'{e["source"]}→{e["target"]}: {e["weight"]}' for e in nc['cycle_edges']) + f'. São {nc["affected_count"]} vértices sem mínimo finito, {nc["unreachable_count"]} inalcançáveis e {nc["finite_count"]} com mínimo finito. Repetir o ciclo soma {nc["cycle_cost"]} a cada volta; não representa lucro financeiro.')

    r.page('19. Desempenho por tarefa obrigatória')
    r.p(f'Cada média e mediana abaixo usa {p2["repetitions"]} execuções. A fonte e o destino determinam a tarefa. Dijkstra inclui busca completa da fonte e reconstrução do par; não é medição de parada antecipada no destino. BFS/DFS são medidos separadamente para cada fonte.')
    r.table(['Algoritmo', 'Fonte', 'Destino', 'Caso', 'Média (s)', 'Mediana (s)'], [
        [x['algorithm'], x['source'], x['target'] if x['target'] is not None else '-',
         'DAG' if 'DAG' in x['case'] else ('ciclo original' if x['algorithm'] == 'Bellman-Ford' else ('par 10-rating' if x['algorithm'] == 'Dijkstra' else 'travessia original')),
         _num(x['mean_seconds'], 7), _num(x['median_seconds'], 7)] for x in p2['case_benchmarks']], [1.6, .7, .8, 1.8, 1.3, 1.3])
    r.p(f'O caso Bellman-Ford na rede original reutiliza as {p2["repetitions"]} medições de mesma fonte/tarefa do benchmark de 100%; não conta novas amostras adicionais. measurement_origin e as séries individuais preservam essa origem em case_benchmarks.csv e no JSON.')
    env = p2['environment']
    r.p(f'Ambiente: Python {env["python"]} ({env["implementation"]}), {env["platform"]}, {env["processor"]}. Cronômetro: {env["timer"]}. Registro UTC: {env["timestamp_utc"]}.')
    r.p('O intervalo medido inclui construir o resultado da busca e detectar/propagar ciclos. Exclui leitura do CSV, construção dos modelos e renderização. Não houve descarte de aquecimento, remoção de outlier temporal ou timeout oculto. Carga de fundo não foi controlada; estes números não são previsão para outra máquina.')

    r.page('20. Escalabilidade e complexidades')
    r.p('Subgrafos induzidos aninhados foram criados por IDs ordenados, embaralhados com random.Random(42), e prefixos de 10%, 50% e 100%. Foram mantidos nós isolados e todos os arcos entre nós selecionados. Não houve amostragem direta de arestas.')
    r.table(['Nós %', 'V', 'E', 'Algoritmo', 'Fonte', 'Média (s)', 'Mediana (s)', 'Mín.-máx. (s)'], [
        [f'{x["fraction"]:.0%}', x['nodes'], x['edges'], x['algorithm'], x['source'], _num(x['mean_seconds'], 6),
         _num(x['median_seconds'], 6), f'{x["min_seconds"]:.6f}-{x["max_seconds"]:.6f}'] for x in p2['benchmarks']],
        [.8, .8, .9, 1.5, .7, 1.15, 1.15, 2])
    r.p('Fontes BFS/DFS/Dijkstra: maior saída do subgrafo. BF prefere menor ID participante de ciclo recíproco negativo; na ausência usa maior saída. As fontes diferem conforme a tarefa, portanto o gráfico não deve ser lido como competição universal com trabalho idêntico.')
    r.table(['Algoritmo', 'Complexidade de tempo', 'Leitura dos resultados'], [
        ['BFS / DFS', 'O(V+E)', 'Varrem a estrutura alcançável; saída e classificação também custam tempo.'],
        ['Dijkstra com heap', 'O((V+E) log V)', 'Relaxamentos e fila de prioridades, somente no modelo 10-rating.'],
        ['Bellman-Ford', 'O(VE)', 'Varreduras repetidas; ciclos negativos exigem detecção e propagação.'],
    ], [1.3, 1.8, 3.3])
    small, large = p2['benchmarks'][0], p2['benchmarks'][-1]
    r.p(f'De {small["nodes"]} para {large["nodes"]} nós, os arcos crescem de {small["edges"]} para {large["edges"]}, não linearmente com a fração de nós. O crescimento mais forte de BF é compatível com seu pior caso, mas três tamanhos, {p2["repetitions"]} execuções e subgrafos diferentes não demonstram empiricamente uma lei assintótica. A mediana reduz a influência descritiva de execuções lentas; a média exigida e todos os valores são preservados.')

    def figure(index, max_height):
        fig = p2['figures'][index - 1]
        r.image(p2dir / fig['file'], f'Figura {index + 5}. ' + fig['caption'], max_height)
        r.p(notes[index], 'small')

    r.page('21. Exploração: distribuição e relações de grau')
    figure(1, 180)
    figure(2, 205)

    r.page('22. Exploração: alcance e tempo')
    figure(3, 180)
    figure(4, 180)
    r.p('As distribuições têm papéis diferentes: quantidade de avaliações não é quantidade de pessoas, alcance dirigido não mede confiança e contagem de negativas depende da exposição. A exploração multivariada usa entrada, saída, negativas recebidas e mês, com IDs tratados apenas como identificadores.', 'small')

    r.page('23. Da exploração à explicação: objetivos de caminho')
    r.p('A exploração encontrou predominância de ratings positivos, mas também negativos e concentração de avaliações. A mesma rede permite perguntar por alcance ou por custo. Para comunicar essa distinção, o primeiro gráfico explanatório compara os mesmos pares sob duas funções objetivas e expõe o número de arcos e o custo transformado.')
    figure(5, 350)
    r.p('A seleção de pares é determinística e não pretende representar todos os caminhos da rede. Barras lado a lado e categorias iguais permitem comparar o mesmo par. Painéis separados evitam misturar unidades; a cor distingue o algoritmo/objetivo. A mensagem é uma troca verificável entre arcos e custo, sem recomendar confiança transitiva.')

    r.page('24. Da exploração à explicação: existência do mínimo')
    r.p(f'A minoria de ratings negativos observada na exploratória motivou verificar se a soma mínima é bem definida. A história principal é local e algorítmica: {len(nc["cycle_edges"])} arcos reais, somando {nc["cycle_cost"]}, bastam para impedir mínimo finito na região alcançável após o ciclo. Uma rede majoritariamente positiva ainda pode ter esse problema.')
    figure(6, 310)
    r.p('O diagrama escolhe somente os vértices e pesos do ciclo conferido, para que direção e soma sejam verificáveis. O painel de controle distingue a rede original de uma rede com arcos removidos e camada crescente. Cor e posição separam os dois casos; números identificam nós/arcos e negativos preservados.')
    r.p(f'A figura responde à terceira parte da pergunta: no controle acíclico, os destinos alcançados têm soma mínima finita apesar dos pesos negativos; na rede original, os {nc["affected_count"]} vértices afetados da fonte {nc["source"]} não têm mínimo finito. Destinos inalcançáveis continuam sendo uma terceira situação distinta.')

    r.page('25. Comparação visual do custo computacional')
    figure(7, 190)
    figure(8, 190)
    r.p('As figuras usam medianas e intervalos, enquanto as tabelas anteriores registram também as médias exigidas. Escalas logarítmicas permitem mostrar tempos muito diferentes, e os eixos/rótulos mantêm a unidade segundo. Leituras e preparação dos modelos não estão nos tempos.', 'small')

    r.page('26. Discussão, limites e participação')
    reach_summary = '; '.join(f'fonte {t["source"]}: {t["reachable"]}/{ds["nodes"]}' for t in p2['traversals'])
    r.p(f'Resposta à pergunta: alcance dirigido ({reach_summary}), com camadas e profundidades específicas de cada fonte. As avaliações positivas são {ds["sign_counts"]["positive"] / ds["rows"]:.2%} dos registros e as negativas {ds["sign_counts"]["negative"] / ds["rows"]:.2%}; a minoria negativa forma um ciclo real de soma {nc["cycle_cost"]}. No modelo original da fonte {nc["source"]}, {nc["affected_count"]} destinos não têm mínimo finito. No controle DAG, conservar {acyclic["negative_edges"]} pesos negativos ainda permite resposta finita porque não há ciclo. Dijkstra responde a outro objetivo, a soma de 10-rating.')
    r.p('Adequação: BFS para menor número de relações; DFS para estrutura e ciclos; Dijkstra para custos não negativos bem definidos; Bellman-Ford para negativos e diagnóstico de ausência de mínimo. A confiabilidade do modelo vem antes da velocidade. Menor saldo de avaliações não mede confiança, e os dados históricos não sustentam causalidade, identidade ou generalização a outras plataformas.')
    r.p(f'Limites de versão: {ds["version_note"]} Aprovação é informação fornecida, sem documento anexado. Zero ausências não prova completude. Outliers foram mantidos. Só três tamanhos e {p2["repetitions"]} execuções não comprovam complexidade assintótica. Resultados calculados não comprovam domínio dos integrantes nem ensaio de defesa.')
    r.sub('Matriz de contribuição comprovada nesta produção')
    r.table(['Pacote', 'Produção observada', 'Dono humano', 'Revisor humano'], [
        ['Modelagem e algoritmos', 'Geração assistida integralmente por IA', 'Não comprovado', 'Não comprovado'],
        ['Mapas, soluções e testes', 'Geração/execução assistidas por IA', 'Não comprovado', 'Não comprovado'],
        ['Dataset, análise e figuras', 'Arquivo recebido; processamento e análise por IA', 'Não comprovado', 'Não comprovado'],
        ['Manual, relatório e declaração', 'Geração assistida integralmente por IA', 'Não comprovado', 'Não comprovado'],
    ], [1.5, 2.7, 1.2, 1.2])
    r.p('Os cinco nomes identificam o grupo informado. Não foram atribuídos commits, tarefas, revisões, assinaturas ou reflexão pessoal sem evidência. A exigência de cada integrante atuar em ao menos dois pacotes não está comprovada por este relatório. A produção com IA inclui usos proibidos; a minuta anexa os registra e deixa cinco assinaturas vazias.')
    r.sub('Referências e reprodutibilidade')
    r.p('Enunciado: docs/referencias/Projeto_Final_TEORIADOSGRAFOS262-1.pdf. Rubrica: docs/referencias/CRITERIOS_PROJETO_2026-2.pdf. Fonte: Stanford SNAP, Bitcoin Alpha; Kumar et al. (ICDM 2016). Evidências completas: out/parte1/ e out/parte2/. O comando python -m src.cli --report recompõe Markdown, PDFs e roteiro a partir desses resultados, sem repetir medições.', 'small')
    return report, p1, p2


def _declaration():
    r = Report('Declaração de uso de IA - minuta não assinada')
    r.page('MINUTA NÃO ASSINADA\nRegistro de uso integral de IA')
    r.p('G1 - Turma 5B - Teoria dos Grafos e Análise e Visualização de Dados - 2026.2')
    r.p('Este arquivo foi gerado por IA. Não é o modelo oficial da professora, que não foi fornecido, não contém assinatura e não constitui declaração aceita ou validada pelas docentes.', 'notice')
    r.p('Integrantes informados: ' + '; '.join(MEMBERS) + '.')
    r.sub('Ferramenta e abrangência observadas')
    r.p('OpenAI Codex foi usado para produzir integralmente código, construção dos grafos, implementações de BFS, DFS, Dijkstra e Bellman-Ford, mapas próprios, testes, execução das soluções, exportações, seleção e criação dos gráficos, análises, notas analíticas, demonstração do m05, discussões, conclusões, manual, relatório e roteiro. As medições e os arquivos de saída são resultados das execuções locais do código gerado, não estimativas inventadas.')
    r.sub('Usos efetivamente realizados que o enunciado proíbe')
    r.table(['Uso realizado', 'Situação no enunciado'], [
        ['Gerar os quatro algoritmos e a construção do grafo de estados', 'Proibido'],
        ['Resolver os mapas fornecidos e os mapas próprios', 'Proibido'],
        ['Gerar prova do m05, análises, discussões, conclusões e notas analíticas', 'Proibido'],
        ['Interpretar os gráficos, escolher tipos e destaques e construir a história explanatória', 'Proibido'],
    ], [4.2, 1.2])
    r.p('A declaração desses usos não elimina a incompatibilidade com as regras. Este material não deve ser apresentado como trabalho autoral humano permitido pela disciplina. O enunciado também exige que integrantes expliquem o que entregam; este registro não comprova que qualquer integrante domine o conteúdo.')
    r.p('Os arquivos de código incluem marcações [IA]. O histórico produzido não será descrito como contribuições humanas. A escolha e aprovação do dataset foram informadas por Artur; participação técnica individual, revisões humanas e assinaturas não foram comprovadas nesta produção.')

    r.page('Ciência e assinaturas - campos em branco')
    r.p('MINUTA NÃO ASSINADA - esta página não contém aceites, datas preenchidas ou assinaturas. Cada pessoa deve ler, conferir os usos reais e decidir pessoalmente sobre eventual assinatura em documento adequado. A substituição pelo modelo oficial e qualquer decisão acadêmica dependem das docentes.')
    r.table(['Integrante informado', 'Participação individual comprovada', 'Assinatura'],
            [[name, 'Não comprovada nesta produção', '\n\n________________________\n\n'] for name in MEMBERS], [1.5, 2.1, 2.4])
    r.p('Local e data: ____________________________________________________')
    r.sub('Pendências explícitas')
    r.p('Obter e preencher o modelo oficial; registrar contribuições e revisões humanas reais com evidências; revisar a incompatibilidade dos usos de IA com as regras; realizar estudo e defesa pessoalmente; colher somente assinaturas autênticas caso as pessoas concordem com o registro. Nenhuma dessas ações é simulada por este PDF.')
    r.p('Referência: seção Uso de IA generativa do enunciado em docs/referencias/Projeto_Final_TEORIADOSGRAFOS262-1.pdf. Esta minuta não promete aceitação, nota ou autorização de entrega.')
    return r


def _script(p1, p2):
    terrain = p1['m01_terreno']['solutions']
    impossible = p1['m07_impossivel']['metrics']
    trap = p1['g1_02_queda_sem_volta']['metrics']
    ds = p2['dataset']
    bf = p2['bellman_ford_cases']
    pair = p2['dijkstra_cases'][0]
    repetitions = p2['repetitions']
    return '\n'.join([
        '# Roteiro de apresentação e estudo - G1 / 5B', '',
        NOTICE, '',
        'Este roteiro foi gerado por IA. Não é relato de estudo, participação ou domínio dos integrantes. A divisão abaixo é por assunto; nenhum apresentador humano foi atribuído.', '',
        '## Preparação real antes da defesa', '',
        'Ler o código e os resultados; conferir os exemplos à mão; executar os comandos do README; explicar os caminhos sem decorar o texto; pedir orientação às docentes sobre os usos proibidos de IA. Não afirmar que houve essa preparação sem realizá-la.', '',
        '## Sequência sugerida: 18 minutos', '',
        '| Tempo | Tema | Demonstração |', '|---|---|---|',
        '| 0-1 min | Objetivo e transparência | Informar produção integral com IA e limites acadêmicos. |',
        '| 1-4 min | Estado, direção e ALVO | Desenhar o mapa mínimo: 7 estados/10 arcos físicos; 8/11 com ALVO. |',
        f'| 4-7 min | Algoritmos nos labirintos | m01: BFS {terrain["BFS"]["steps"]}/{terrain["BFS"]["cost"]} e Dijkstra {terrain["DIJKSTRA"]["steps"]}/{terrain["DIJKSTRA"]["cost"]}; m05 bônus consumível; m06 ciclo e correção. |',
        f'| 7-9 min | Camadas, armadilhas e mapas G1 | m02 com/sem chave; m07 com {impossible["G_est"]["order"]} estados e nenhuma saída; {trap["traps_count"]}/{trap["G_est"]["order"]} armadilhas no G1-02. |',
        f'| 9-12 min | Dataset e pergunta | Preservar {ds["rows"]}/{ds["nodes"]}; distinguir rating e 10-rating; {len(p2["traversals"])} fontes. |',
        f'| 12-15 min | Figuras e resposta | Predominância positiva, ciclo {bf["original_negative_cycle"]["cycle_cost"]} real e controle DAG com {bf["acyclic_control"]["negative_edges"]} negativos. |',
        f'| 15-17 min | Desempenho e limites | Médias de {repetitions} execuções, três tamanhos e tarefas diferentes. |',
        '| 17-18 min | Execução de mapa e fechamento | Rodar TXT surpresa com --mapa e explicar o estado/custo/status. |', '',
        '## Comandos de demonstração', '', '```powershell',
        'python -m src.cli --mapa data/mapas/m01_terreno.txt --alg BFS --out out/demo',
        'python -m src.cli --mapa data/mapas/m01_terreno.txt --alg DIJKSTRA --out out/demo',
        'python -m src.cli --mapa data/mapas/m05_bonus.txt --alg BELLMAN_FORD --out out/demo',
        'python -m src.cli --mapa data/mapas/m06_fonte.txt --alg BELLMAN_FORD --out out/demo',
        'python -m src.cli --mapa data/mapas/m06_fonte.txt --alg BELLMAN_FORD --fonte-consumivel --out out/demo_corrigida',
        'python -m src.cli --mapa data/mapas/m07_impossivel.txt --armadilhas --out out/demo',
        f'python -m src.cli --dataset data/dataset_parte2 --alg DIJKSTRA --source {pair["source"]} --target {pair["target"]} --out out/demo_dataset',
        '```', '',
        'Abrir out/parte1/labirinto_interativo.html. Avançar manualmente pelo percurso, trocar a camada e destacar armadilhas. Não narrar um status de recusa ou ciclo como se fosse um ótimo finito.', '',
        '## Perguntas para conferir entendimento individual', '',
        '1. Por que duas visitas à mesma casa podem ser nós diferentes?',
        '2. Por que não há estado sem chave na casa a do mapa mínimo?',
        '3. Por que G tem arco para ALVO, mas nenhum movimento físico de saída?',
        '4. Por que BFS usa mais custo em m01 mesmo com menos passos?',
        '5. Por que o consumo monotônico de bônus elimina ciclos negativos no m05?',
        '6. Por que fonte consumível ainda leva Dijkstra a recusar o grafo?',
        '7. Como o transposto distingue armadilha de beco?',
        '8. Por que minimizar 10-rating não equivale a minimizar rating?',
        '9. Como a camada estritamente crescente prova que o controle é DAG?',
        f'10. Qual evidência valida o ciclo {"→".join(map(str, bf["original_negative_cycle"]["negative_cycle"]))} e quais destinos ele afeta?',
        '11. O que foi medido nos tempos, o que ficou fora e por que as tarefas não são equivalentes?',
        '12. Que informações não são autorizadas pelos dados (causalidade, identidade, confiança transitiva)?', '',
        '## Materiais a consultar', '',
        'docs/RELATORIO_TECNICO.pdf e .md; out/parte1/resultados.json; out/parte2/parte2_report.json; CSV de tempos individuais; notas analíticas e figuras em out/parte2/. A declaração é minuta não assinada. A participação individual permanece não comprovada.', '',
    ])


def generate_reports(root, out_base):
    """Recria manual/relatório, minuta de declaração e roteiro dos arquivos de out.

    Não altera fontes de dados, não atribui contribuição humana e não executa
    novamente os algoritmos. Imagens ausentes e notas incompletas geram erro.
    """
    root, out = Path(root).resolve(), Path(out_base).resolve()
    docs = root / 'docs'
    docs.mkdir(parents=True, exist_ok=True)
    report, p1, p2 = _report(root, out)
    report.markdown(docs / 'RELATORIO_TECNICO.md')
    report.pdf(docs / 'RELATORIO_TECNICO.pdf')
    _declaration().pdf(docs / 'DECLARACAO_IA.pdf', declaration=True)
    (docs / 'ROTEIRO_APRESENTACAO.md').write_text(_script(p1, p2), encoding='utf-8')
    print('Documentos gerados: relatório técnico/manual, minuta IA não assinada e roteiro.', flush=True)
    return {name: str(docs / name) for name in ['RELATORIO_TECNICO.md', 'RELATORIO_TECNICO.pdf',
                                               'DECLARACAO_IA.pdf', 'ROTEIRO_APRESENTACAO.md']}
