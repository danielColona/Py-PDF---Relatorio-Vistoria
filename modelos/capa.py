"""
Desenho da capa do relatório (primeira página).
"""

from datetime import date

from reportlab.lib.units import mm

from . import layout


def desenhar_capa(canvas, config):

    largura, altura = layout.PAGINA
    canvas.saveState()

    # Fundo customizado (recursos/Capa_Fundo.png), se existir — cobre a
    # página inteira, por baixo do logo/título/texto desenhados a seguir.
    fundo = config.logo.parent / "Capa_Fundo.png"
    if fundo.exists():
        try:
            canvas.drawImage(
                str(fundo),
                0, 0,
                width=largura,
                height=altura,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception:
            pass

    # Logo (se existir) — bem maior, já que é PNG sem fundo
    #if config.logo.exists():
     #   try:
      #      canvas.drawImage(
       #         str(config.logo),
        #        largura / 2 - 55 * mm,
         #       altura - 95 * mm,
          #      width=110 * mm,
           #     height=55 * mm,
            #    preserveAspectRatio=True,
             #   mask="auto",
            #)
        #except Exception:
         #   pass

    canvas.setFillColor(layout.COR_TITULO)
    canvas.setFont(layout.FONTE_TITULO_CAPA, layout.TAMANHO_TITULO_CAPA)
    canvas.drawCentredString(largura / 2, altura / 2 + 8, config.titulo)

    canvas.setStrokeColor(layout.COR_LINHA)
    canvas.setLineWidth(2)
    canvas.line(largura / 2 - 60, altura / 2 - 4, largura / 2 + 60, altura / 2 - 4)

    canvas.setFillColor(layout.COR_TEXTO_CLARO)
    canvas.setFont("Helvetica", 13)
    canvas.drawCentredString(largura / 2, altura / 2 - 22, config.empresa)
    canvas.drawCentredString(
        largura / 2, altura / 2 - 38, f"{config.cidade} / {config.estado}"
    )

    canvas.setFont("Helvetica", 9)
    canvas.drawCentredString(
        largura / 2, 30, f"Gerado em {date.today().strftime('%d/%m/%Y')}"
    )

    canvas.restoreState()


def desenhar_contracapa(canvas, config, itens):
    """
    Página divisória entre grupos de categorias (ex: Segurança/Zeladoria
    antes de Organização/Infra). `itens` é uma lista de (titulo, chave_link)
    — cada item vira uma linha clicável que pula direto pra aquela seção.
    """
    largura, altura = layout.PAGINA
    canvas.saveState()

    if config.logo.exists():
        try:
            canvas.drawImage(
                str(config.logo),
                largura / 2 - 45 * mm,
                altura - 78 * mm,
                width=90 * mm,
                height=45 * mm,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception:
            pass

    titulo_grupo = " / ".join(titulo.upper() for titulo, _ in itens)
    canvas.setFillColor(layout.COR_TITULO)
    canvas.setFont(layout.FONTE_TITULO_CAPA, 22)
    canvas.drawCentredString(largura / 2, altura / 2 + 6, titulo_grupo)

    canvas.setStrokeColor(layout.COR_LINHA)
    canvas.setLineWidth(2)
    canvas.line(largura / 2 - 60, altura / 2 - 10, largura / 2 + 60, altura / 2 - 10)

    y = altura / 2 - 34
    canvas.setFont("Helvetica-Bold", 14)
    for titulo, chave in itens:
        texto = titulo.upper()
        canvas.setFillColor(layout.COR_LINHA)
        canvas.drawCentredString(largura / 2, y, texto)

        largura_texto = canvas.stringWidth(texto, "Helvetica-Bold", 14)
        canvas.linkRect(
            "", chave,
            (largura / 2 - largura_texto / 2 - 4, y - 4,
             largura / 2 + largura_texto / 2 + 4, y + 14),
            relative=0, thickness=0,
        )
        y -= 26

    canvas.restoreState()