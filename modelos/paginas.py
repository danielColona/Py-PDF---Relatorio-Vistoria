"""
Construção do corpo do relatório: um título por pasta + fotos,
percorrendo a árvore de Secao (util.leitor) recursivamente.

As fotos de cada seção são divididas em blocos de até 4, e cada
bloco escolhe o template que melhor aproveita o espaço da página:

  1 foto  -> uma foto grande, centralizada
  2 fotos -> duas fotos lado a lado
  3 fotos -> escolhido pela orientação real das fotos:
               3 retrato  -> 3 colunas iguais
               3 paisagem -> 2 em cima + 1 embaixo
               mistura    -> 1 em destaque + 2 menores empilhadas
  4 fotos -> grade 2x2

Cada seção que tem fotos próprias começa em página nova; se tiver
mais de 4 fotos, os blocos seguintes também começam em página nova
(com um rótulo "(continuação)").
"""

from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm

from . import layout
from .planejador_fotos import planejar_blocos
from util.parser import titulo_amigavel, legenda_da_foto
from util.imagens import dimensoes_ajustadas, preparar_para_pdf, orientacao


# =====================================================
# Estilos de título
# =====================================================

def estilos_secao():
    return {
        1: ParagraphStyle(
            "SecaoNivel1", fontName=layout.FONTE_NIVEL1,
            fontSize=layout.TAMANHO_NIVEL1,
            textColor=layout.COR_TEXTO_NIVEL1, backColor=layout.COR_FUNDO_NIVEL1,
            leading=layout.TAMANHO_NIVEL1 + 4,
            spaceBefore=0, spaceAfter=16,
            borderPadding=9,
        ),
        2: ParagraphStyle(
            "SecaoNivel2", fontName=layout.FONTE_NIVEL2,
            fontSize=layout.TAMANHO_NIVEL2,
            textColor=layout.COR_TEXTO_NIVEL2, backColor=layout.COR_FUNDO_NIVEL2,
            leading=layout.TAMANHO_NIVEL2 + 3,
            spaceBefore=4, spaceAfter=12,
            leftIndent=6, rightIndent=6,
            borderPadding=6,
        ),
        3: ParagraphStyle(
            "SecaoNivel3", fontName=layout.FONTE_NIVEL3,
            fontSize=layout.TAMANHO_NIVEL3, textColor=layout.COR_TEXTO_NIVEL3,
            leading=layout.TAMANHO_NIVEL3 + 3,
            spaceBefore=4, spaceAfter=8, leftIndent=14,
        ),
        4: ParagraphStyle(
            "SecaoNivel4", fontName=layout.FONTE_NIVEL4,
            fontSize=layout.TAMANHO_NIVEL4, textColor=layout.COR_TEXTO_NIVEL4,
            leading=layout.TAMANHO_NIVEL4 + 3,
            spaceBefore=2, spaceAfter=6, leftIndent=22,
        ),
    }


def _estilo_repeticao(estilo_original):
    """
    Clone do estilo original só com nome diferente — usado quando o
    título de um ancestral (Contêiner, Fila) é repetido no topo de uma
    nova página como referência visual. Precisa ter um nome diferente
    de 'SecaoNivelN' para o afterFlowable não registrar essa repetição
    como se fosse uma entrada nova no sumário/marcadores.
    """
    return ParagraphStyle(f"{estilo_original.name}Repeticao", parent=estilo_original)


_ESTILO_LEGENDA = ParagraphStyle(
    "Legenda", fontName=layout.FONTE_LEGENDA, fontSize=layout.TAMANHO_LEGENDA,
    alignment=1, textColor=layout.COR_TEXTO_CLARO, spaceBefore=3,
)

# =====================================================
# Percurso da árvore de seções
# =====================================================

_ALTURA_POR_NIVEL = {
    1: layout.ALTURA_TITULO_NIVEL1,
    2: layout.ALTURA_TITULO_NIVEL2,
    3: layout.ALTURA_TITULO_NIVEL3,
    4: layout.ALTURA_TITULO_NIVEL4,
}


def construir_flowables(secoes, config, largura_disponivel, altura_total_frame,
                         estilos=None, progresso=None, _estado=None, _caminho=None,
                         _categoria=None):
    """
    Percorre a árvore de seções e retorna a lista de flowables do corpo do PDF.

    _caminho guarda a trilha de ancestrais (nível, título) ainda "abertos" —
    usada para repetir Contêiner/Fila no topo da página de Fila/Rack, dando
    noção de onde aquela foto está dentro da estrutura.
    """
    if estilos is None:
        estilos = estilos_secao()

    if _estado is None:
        _estado = {"tem_conteudo": False, "titulos_na_pagina": []}

    if _caminho is None:
        _caminho = []

    elementos = []

    for secao in secoes:
        categoria = _categoria if _categoria is not None else secao.nome
        titulo = titulo_amigavel(secao.nome)
        estilo = estilos.get(secao.nivel, estilos[4])

        # Só quebra a página se JÁ houver fotos desenhadas na página atual —
        # senão o título de uma categoria (Segurança, Zeladoria...) ficaria
        # sozinho numa página em branco. Categorias de topo (nível 1) sempre
        # abrem página nova quando trocam de categoria, mas o primeiro filho
        # (ex: Fachada) continua na mesma página, logo abaixo do título.
        precisa_pagina_nova = _estado["tem_conteudo"] and (
            secao.nivel == 1 or bool(secao.imagens)
        )

        if precisa_pagina_nova:
            elementos.append(PageBreak())
            _estado["tem_conteudo"] = False
            _estado["titulos_na_pagina"] = []

            # Repete a trilha de Contêiner/Fila (sem repetir a categoria de
            # topo, que já apareceu lá atrás) no início da nova página, para
            # dar noção de referência de onde essas fotos estão.
            for nivel_ancestral, titulo_ancestral in _caminho:
                if nivel_ancestral == 1:
                    continue
                estilo_ancestral = _estilo_repeticao(
                    estilos.get(nivel_ancestral, estilos[4])
                )
                elementos.append(Paragraph(titulo_ancestral, estilo_ancestral))
                _estado["titulos_na_pagina"].append(nivel_ancestral)

        elementos.append(Paragraph(titulo, estilo))
        _estado["titulos_na_pagina"].append(secao.nivel)

        if secao.imagens:
            reserva = sum(
                _ALTURA_POR_NIVEL.get(n, layout.ALTURA_TITULO_NIVEL4)
                for n in _estado["titulos_na_pagina"]
            ) + layout._MARGEM_SEGURANCA_TITULOS
            altura_disponivel = altura_total_frame - reserva

            elementos.extend(
                _blocos_de_fotos(
                    secao.imagens, titulo, estilo, categoria, config,
                    largura_disponivel, altura_disponivel, progresso,
                )
            )
            _estado["tem_conteudo"] = True

        if secao.subsecoes:
            elementos.extend(
                construir_flowables(
                    secao.subsecoes, config, largura_disponivel, altura_total_frame,
                    estilos, progresso, _estado, _caminho + [(secao.nivel, titulo)], categoria,
                )
            )

    return elementos


# =====================================================
# Divisão em blocos de até 4 fotos + escolha do template
# =====================================================

def _blocos_de_fotos(imagens, titulo_secao, estilo_secao, categoria, config,
                     largura, altura, progresso):
    elementos = []
    grupos = planejar_blocos(imagens)

    for indice, grupo in enumerate(grupos):
        if indice > 0:
            elementos.append(PageBreak())
            # Repete o próprio título com a mesma aparência, sem criar uma
            # nova entrada no sumário ou nos marcadores do PDF.
            elementos.append(Paragraph(titulo_secao, _estilo_repeticao(estilo_secao)))

        elementos.append(_montar_bloco(grupo, categoria, config, largura, altura, progresso))
        elementos.append(Spacer(1, 4 * mm))

    return elementos


def _montar_bloco(fotos, categoria, config, largura, altura, progresso):
    n = len(fotos)
    if n == 1:
        return _layout_1(fotos, categoria, config, largura, altura, progresso)
    if n == 2:
        if any(orientacao(foto) != "retrato" for foto in fotos):
            raise ValueError("Template 04 requer exatamente 2 fotos retrato.")
        return _layout_2(fotos, categoria, config, largura, altura, progresso)
    if n == 3:
        return _layout_3(fotos, categoria, config, largura, altura, progresso)
    if any(orientacao(foto) != "paisagem" for foto in fotos):
        raise ValueError("Template 01 requer exatamente 4 fotos paisagem.")
    return _layout_4(fotos, categoria, config, largura, altura, progresso)


# =====================================================
# Templates
# =====================================================

def _celula(caminho, categoria, config, largura_caixa, altura_caixa, progresso):
    altura_foto_max = max(altura_caixa - layout.ALTURA_LEGENDA - 4, 10)

    try:
        largura_foto, altura_foto = dimensoes_ajustadas(
            caminho, largura_caixa, altura_foto_max
        )
        buffer = preparar_para_pdf(caminho, largura_foto, altura_foto)
        img = Image(buffer, width=largura_foto, height=altura_foto)
        img.hAlign = "CENTER"
    except Exception as erro:
        print(f"\n  [aviso] Não foi possível ler '{caminho.name}': {erro}. Pulando essa foto.")
        img = Paragraph("(foto indisponível)", _ESTILO_LEGENDA)

    if progresso:
        progresso.avancar()

    legenda = legenda_da_foto(caminho, config.prefixo_arquivos, categoria)
    return [img, Paragraph(legenda, _ESTILO_LEGENDA)]


def _estilo_base(gap):
    return [
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), gap / 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), gap / 2),
    ]


def _layout_1(fotos, categoria, config, largura, altura, progresso):
    largura_cel = largura * 0.8
    celula = _celula(fotos[0], categoria, config, largura_cel, altura, progresso)

    tabela = Table([[celula]], colWidths=[largura], rowHeights=[altura])
    tabela.setStyle(TableStyle(_estilo_base(0)))
    return tabela


def _layout_2(fotos, categoria, config, largura, altura, progresso):
    gap = layout.ESPACO_ENTRE_FOTOS

    # Fotos retrato costumam ser bem estreitas/altas e já batem no teto de
    # altura disponível bem antes de usar toda a largura de uma coluna de
    # meia página — sobrava muito vazio nas laterais. Usa a mesma largura
    # de coluna do Template 05 (3 fotos) como referência e centraliza o
    # par na página, em vez de esticar a coluna pra metade da largura.
    largura_cel = (largura - 2 * gap) / 3

    linha = [_celula(f, categoria, config, largura_cel, altura, progresso) for f in fotos]

    tabela = Table([linha], colWidths=[largura_cel] * 2, rowHeights=[altura])
    tabela.setStyle(TableStyle(_estilo_base(gap)))
    tabela.hAlign = "CENTER"
    return tabela


def _layout_4(fotos, categoria, config, largura, altura, progresso):
    gap = layout.ESPACO_ENTRE_FOTOS
    largura_cel = (largura - gap) / 2
    altura_cel = (altura - gap) / 2

    linhas = [
        [_celula(fotos[0], categoria, config, largura_cel, altura_cel, progresso),
         _celula(fotos[1], categoria, config, largura_cel, altura_cel, progresso)],
        [_celula(fotos[2], categoria, config, largura_cel, altura_cel, progresso),
         _celula(fotos[3], categoria, config, largura_cel, altura_cel, progresso)],
    ]

    tabela = Table(linhas, colWidths=[largura_cel] * 2, rowHeights=[altura_cel] * 2)
    tabela.setStyle(TableStyle(_estilo_base(gap)))
    return tabela


def _layout_3(fotos, categoria, config, largura, altura, progresso):
    """Escolhe o template de 3 fotos com base na orientação real de cada uma."""
    orientacoes = [orientacao(f) for f in fotos]

    if orientacoes.count("retrato") == 3:
        return _layout_3_colunas(fotos, categoria, config, largura, altura, progresso)

    if orientacoes.count("paisagem") == 3:
        return _layout_3_topo_base(fotos, categoria, config, largura, altura, progresso)

    return _layout_3_destaque(fotos, orientacoes, categoria, config, largura, altura, progresso)


def _layout_3_colunas(fotos, categoria, config, largura, altura, progresso):
    """3 fotos retrato -> 3 colunas iguais."""
    gap = layout.ESPACO_ENTRE_FOTOS
    largura_cel = (largura - 2 * gap) / 3

    linha = [_celula(f, categoria, config, largura_cel, altura, progresso) for f in fotos]

    tabela = Table([linha], colWidths=[largura_cel] * 3, rowHeights=[altura])
    tabela.setStyle(TableStyle(_estilo_base(gap)))
    return tabela


def _layout_3_topo_base(fotos, categoria, config, largura, altura, progresso):
    """3 fotos paisagem -> 2 em cima + 1 embaixo (célula vazia no canto)."""
    gap = layout.ESPACO_ENTRE_FOTOS
    largura_cel = (largura - gap) / 2
    altura_topo = (altura - gap) * 0.55
    altura_base = (altura - gap) * 0.45

    linha1 = [
        _celula(fotos[0], categoria, config, largura_cel, altura_topo, progresso),
        _celula(fotos[1], categoria, config, largura_cel, altura_topo, progresso),
    ]
    linha2 = [
        _celula(fotos[2], categoria, config, largura_cel, altura_base, progresso),
        "",
    ]

    tabela = Table(
        [linha1, linha2],
        colWidths=[largura_cel] * 2,
        rowHeights=[altura_topo, altura_base],
    )
    tabela.setStyle(TableStyle(_estilo_base(gap)))
    return tabela


def _layout_3_destaque(fotos, orientacoes, categoria, config, largura, altura, progresso):
    """Mistura de orientações -> 1 foto em destaque + 2 menores empilhadas.

    Template 03: 1 retrato em destaque à esquerda e 2 paisagens empilhadas
    à direita.
    """
    if orientacoes.count("retrato") != 1 or orientacoes.count("paisagem") != 2:
        raise ValueError("Template 03 requer exatamente 1 retrato e 2 paisagens.")

    # Template 03: retrato grande na coluna esquerda; paisagens empilhadas
    # na coluna direita, como definido no modelo aprovado.
    indice_destaque = orientacoes.index("retrato")

    indices_pequenas = [i for i in range(3) if i != indice_destaque]

    gap = layout.ESPACO_ENTRE_FOTOS
    largura_cel = (largura - gap) / 2
    altura_pequena = (altura - gap) / 2

    celula_p1 = _celula(fotos[indices_pequenas[0]], categoria, config, largura_cel, altura_pequena, progresso)
    celula_p2 = _celula(fotos[indices_pequenas[1]], categoria, config, largura_cel, altura_pequena, progresso)
    celula_destaque = _celula(fotos[indice_destaque], categoria, config, largura_cel, altura, progresso)

    linhas = [
        [celula_destaque, celula_p1],
        ["", celula_p2],
    ]

    tabela = Table(
        linhas,
        colWidths=[largura_cel, largura_cel],
        rowHeights=[altura_pequena, altura_pequena],
    )
    estilo = _estilo_base(gap)
    estilo.append(("SPAN", (0, 0), (0, 1)))
    tabela.setStyle(TableStyle(estilo))
    return tabela
