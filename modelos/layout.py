"""
Todas as constantes visuais do relatório ficam centralizadas aqui.
Mudou o layout? Mexe só neste arquivo.
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor

PAGINA = landscape(A4)
LARGURA_PAGINA, ALTURA_PAGINA = PAGINA

# Margens
MARGEM_ESQUERDA = 12 * mm
MARGEM_DIREITA = 12 * mm
MARGEM_SUPERIOR = 14 * mm
MARGEM_INFERIOR = 12 * mm

# Cabeçalho / rodapé (desenhados dentro das margens acima)
ALTURA_CABECALHO = 10 * mm
ALTURA_RODAPE = 8 * mm

# Fotos: templates dinâmicos (1, 2, 3 ou 4 fotos por página, conforme
# a quantidade e orientação — ver modelos/paginas.py)
ESPACO_ENTRE_FOTOS = 6 * mm
ALTURA_LEGENDA = 10 * mm

# Altura aproximada que cada nível de título ocupa na página (usado para
# calcular dinamicamente quanto espaço sobra para as fotos, já que agora
# vários títulos podem aparecer empilhados — ex: Contêiner + Fila + Rack)
ALTURA_TITULO_NIVEL1 = 24 * mm
ALTURA_TITULO_NIVEL2 = 19 * mm
ALTURA_TITULO_NIVEL3 = 15 * mm
ALTURA_TITULO_NIVEL4 = 13 * mm
_MARGEM_SEGURANCA_TITULOS = 6 * mm

# Cores
COR_TITULO = HexColor("#1a1a2e")
COR_LINHA = HexColor("#c0392b")
COR_TEXTO_CLARO = HexColor("#555555")

# Cores dos "banners" de título de cada nível de seção
COR_FUNDO_NIVEL1 = COR_TITULO
COR_TEXTO_NIVEL1 = HexColor("#ffffff")

COR_FUNDO_NIVEL2 = HexColor("#f2e4e2")
COR_TEXTO_NIVEL2 = COR_TITULO

COR_TEXTO_NIVEL3 = COR_LINHA
COR_TEXTO_NIVEL4 = COR_TEXTO_CLARO

# Fontes
FONTE_TITULO_CAPA = "Helvetica-Bold"
TAMANHO_TITULO_CAPA = 26

FONTE_NIVEL1 = "Helvetica-Bold"
TAMANHO_NIVEL1 = 19

FONTE_NIVEL2 = "Helvetica-Bold"
TAMANHO_NIVEL2 = 14

FONTE_NIVEL3 = "Helvetica-Bold"
TAMANHO_NIVEL3 = 16

FONTE_NIVEL4 = "Helvetica-BoldOblique"
TAMANHO_NIVEL4 = 14

FONTE_LEGENDA = "Helvetica"
TAMANHO_LEGENDA = 11

FONTE_CABECALHO = "Helvetica"
TAMANHO_CABECALHO = 8

FONTE_RODAPE = "Helvetica"
TAMANHO_RODAPE = 8

# Profundidade máxima de pastas que aparece no Sumário impresso
# (3 = Categoria > Contêiner/Fachada > Fila; Racks não entram no sumário
# impresso — com 40+ racks não caberia numa página de jeito nenhum — mas
# continuam navegáveis pelo painel de marcadores lateral do PDF, que não
# ocupa espaço de página)
PROFUNDIDADE_MAXIMA_SUMARIO = 3