"""
Sumário navegável (Table of Contents).

O reportlab preenche esta tabela automaticamente durante o build,
com base nas notificações de 'TOCEntry' disparadas pelo template
do documento (ver relatorio.py) sempre que um título de seção é
desenhado.
"""

from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import ParagraphStyle

from . import layout


def criar_sumario():
    toc = TableOfContents()

    toc.levelStyles = [
        ParagraphStyle(
            name="TOCNivel1",
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=12,
            spaceBefore=5,
            textColor=layout.COR_TITULO,
        ),
        ParagraphStyle(
            name="TOCNivel2",
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=9.5,
            leftIndent=10,
            spaceBefore=1.5,
            textColor=layout.COR_TITULO,
        ),
        ParagraphStyle(
            name="TOCNivel3",
            fontName="Helvetica",
            fontSize=7.5,
            leading=8.5,
            leftIndent=20,
            spaceBefore=0.5,
            textColor=layout.COR_LINHA,
        ),
    ]

    return toc