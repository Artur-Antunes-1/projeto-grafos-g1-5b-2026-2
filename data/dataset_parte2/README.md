# Bitcoin Alpha

## Arquivo recebido

`bitcoinalpha.csv` foi extraído de `archive (28).zip`, fornecido por Artur, sem alterar os bytes do CSV. Artur informou em 01/11/2026 que o dataset escolhido já foi aprovado pelas duas professoras.

O cabeçalho recebido é `,SOURCE,TARGET,RATING,TIME`. A primeira coluna não tem nome e contém um índice sequencial de 0 a 24.184. A fonte SNAP descreve os quatro campos de dados:

- `SOURCE`: identificador de quem avaliou.
- `TARGET`: identificador de quem recebeu a avaliação.
- `RATING`: avaliação de -10 (desconfiança total) a +10 (confiança total).
- `TIME`: instante da avaliação em segundos desde a época Unix.

Esses dados descrevem avaliações dirigidas entre usuários. A escolha de como utilizar ou transformar os pesos nos experimentos será documentada pelo grupo.

## Diferença em relação à fonte original

A conferência técnica encontrou 24.185 registros e 3.782 identificadores distintos na união de `SOURCE` e `TARGET` no arquivo recebido. A versão original da SNAP contém 24.186 registros e 3.783 usuários.

A comparação registro a registro confirmou que o CSV recebido corresponde ao original sem a primeira linha de dados:

```csv
7188,1,10,1407470400
```

Os demais registros coincidem na mesma ordem, desconsiderando o cabeçalho e a coluna de índice adicionados à cópia recebida. A causa da omissão não foi confirmada. O repositório mantém a versão fornecida; o grupo deve registrar qual versão adotará antes dos experimentos e, se necessário, confirmar a alteração com as professoras.

## Referência

- [Página original do dataset — Stanford SNAP](https://snap.stanford.edu/data/soc-sign-bitcoin-alpha.html)
- [Arquivo original compactado](https://snap.stanford.edu/data/soc-sign-bitcoinalpha.csv.gz)
- Kumar, S.; Spezzano, F.; Subrahmanian, V. S.; Faloutsos, C. *Edge Weight Prediction in Weighted Signed Networks*. IEEE ICDM, 2016.

Procedência e hashes dos arquivos: `docs/PROVENIENCIA.json`, na raiz do repositório.
