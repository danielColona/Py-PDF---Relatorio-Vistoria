# RelatorioVistoria

Gerador de relatório fotográfico de vistoria de sites (Claro S/A) em PDF,
a partir de uma pasta de fotos organizada em subpastas. Escrito em Python
com `reportlab` (montagem do PDF) e `Pillow`/`pypdf` (imagens e pós-
processamento do PDF).

## Configuração (`config.json`)

Cada rodada de vistoria/site exige atualizar:

- `pasta_site`: caminho da pasta raiz com as fotos daquele site (estrutura
  esperada: `INFRA/`, `ORGANIZAÇÃO/`, `SEGURANÇA/`, `ZELADORIA/`, cada uma
  com subpastas — ver `estrutura.txt` para um exemplo real). Atualmente
  aponta para OneDrive (`C:\Users\Colona\OneDrive - Claro SA\Área de
  Trabalho\Vistoria Sites\HUB SEA`), não mais para `C:\SITES\...`.
- `site`, `cidade`, `estado`, `titulo`: usados na capa e nos nomes de
  arquivo.

## Como gerar os PDFs

- `python gerar_relatorio.py` — gera só o Book completo (`config.arquivo_pdf`,
  nome derivado de `site`).
- `python gerar_livros.py` — fluxo usado na prática todo mês: gera o Book
  completo (`Book_Vistoria-{MESANO}-{SITE}.pdf`, ex: `AGO26`) e mais 3
  books derivados reaproveitando páginas do completo:
  - `Book_Zeladoria-Vistoria-...` (Segurança + Zeladoria)
  - `Book_Organizacao-Vistoria-...`
  - `Book_Infra-Vistoria-...`

  O sufixo de mês/ano é derivado da data atual (`_mes_ano()` em
  `gerar_livros.py`), não precisa editar nada mês a mês.

### Regra de tamanho dos secundários

Os 3 books derivados (Zeladoria/Organização/Infra) não podem passar de
10MB (`_LIMITE_MB_SECUNDARIOS` em `gerar_livros.py`). O arquivo **original**
de cada um é sempre mantido; se passar do limite, uma versão
`..._compressed.pdf` é gerada automaticamente recomprimindo as imagens
embutidas (reduz resolução/qualidade JPEG em níveis progressivos até
caber). O Book completo (`Book_Vistoria-...`) nunca é comprimido.

### Como a extração dos secundários funciona (importante)

Cada book derivado reaproveita, do Book completo já gerado: página 0
(capa) + página 1 (sumário, sem alterações — continua mostrando todas as
seções, mas só os links da seção presente naquele book funcionam) + o
intervalo de páginas da(s) seção(ões) daquele grupo (contracapa do grupo +
conteúdo).

As páginas são copiadas numa **única chamada** `PdfWriter.append(reader,
pages=lista_combinada)` (não múltiplas chamadas separadas) — o `pypdf` só
remapeia links internos (ex: "↑ Voltar ao Sumário" no cabeçalho, e as
entradas do Sumário) dentro de uma mesma chamada de `append()`. Duas
chamadas separadas quebram esses links. Ver `_extrair_livro()` em
`gerar_livros.py`.

## Arquitetura

- `util/leitor.py` — varre `pasta_site` recursivamente e monta a árvore de
  `Secao` (uma por pasta com fotos, direta ou herdada).
- `util/parser.py` — nomes de pasta → título amigável; nome de arquivo →
  legenda da foto.
- `util/imagens.py` — orientação (retrato/paisagem), correção EXIF,
  redimensionamento/recompressão antes de embutir no PDF.
- `util/config.py` — leitura do `config.json`.
- `modelos/relatorio.py` — orquestrador: monta capa, sumário, contracapas
  por grupo (`GRUPOS_CONTRACAPA`), bookmarks/outline do PDF, e chama
  `paginas.py` para o corpo.
- `modelos/paginas.py` — percorre a árvore de seções e monta as páginas de
  fotos, escolhendo o template (1 a 5, ver `recursos/Templates.png`)
  conforme quantidade/orientação das fotos no bloco.
- `modelos/planejador_fotos.py` — agrupa as fotos de uma seção nos blocos
  válidos (só as combinações dos 5 templates; sobra vira página avulsa).
- `modelos/layout.py` — todas as constantes visuais (cores, fontes,
  margens, tamanhos de título por nível).
- `gerar_livros.py` — orquestra a geração dos 4 books (ver acima).

### Templates de foto (`recursos/Templates.png`)

- T01: 4 fotos paisagem (grade 2x2)
- T02: 3 fotos paisagem (2 em cima + 1 embaixo)
- T03: 1 retrato + 2 paisagem (retrato em destaque + 2 empilhadas)
- T04: 2 fotos retrato lado a lado
- T05: 3 fotos retrato lado a lado

**Decisão de design (2026-08):** no T04, a largura da coluna usa a mesma
referência do T05 (`(largura - 2*gap) / 3`) em vez de metade da página,
com a tabela centralizada (`hAlign="CENTER"`). Fotos retrato reais tendem
a ser estreitas/altas e ficam limitadas pela altura da página bem antes de
usar meia página de largura — isso deixava muito espaço vazio ao redor no
T04. **Não cortar/fazer crop das fotos** — decisão explícita do usuário,
o T05 já funciona bem sem cortar e o T04 deve seguir o mesmo princípio.

## Gotchas / decisões já tomadas

- Windows trava o arquivo PDF enquanto ele está aberto num leitor —
  `_extrair_livro()` levanta `PermissionError` com mensagem clara nesse
  caso; é preciso fechar o arquivo antes de regerar.
- `__pycache__/` e `.venv/` estão no `.gitignore` — não versionar bytecode
  (havia sido versionado por engano nos primeiros commits e depois
  removido).
- `saida/` (pasta de saída dos PDFs) está no `.gitignore` — os PDFs
  gerados não são versionados.
- `pypdf` foi adicionado ao `requirements.txt` (split/compressão dos
  books). `Pillow` já cobria manipulação de imagem.
