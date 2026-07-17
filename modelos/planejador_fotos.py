"""Planejamento de fotos respeitando estritamente os templates do relatório.

Os únicos agrupamentos permitidos são: 4 paisagens; 3 paisagens;
1 retrato + 2 paisagens; 2 retratos; e 3 retratos. Quando uma foto sobra e
não completa nenhum template, ela fica sozinha em uma página de contingência.
"""

from functools import lru_cache

from util.imagens import orientacao


# (paisagens, retratos), na mesma ordem dos templates 01 a 05.
_TEMPLATES = (
    (4, 0),
    (3, 0),
    (2, 1),
    (0, 2),
    (0, 3),
)


def planejar_blocos(imagens):
    """Agrupa fotos somente nas combinações previstas nos templates."""
    paisagens = [foto for foto in imagens if orientacao(foto) == "paisagem"]
    retratos = [foto for foto in imagens if orientacao(foto) == "retrato"]

    grupos = []
    for qtd_paisagens, qtd_retratos in _planejar_composicao(
        len(paisagens), len(retratos)
    ):
        grupo = [paisagens.pop(0) for _ in range(qtd_paisagens)]
        grupo.extend(retratos.pop(0) for _ in range(qtd_retratos))
        grupos.append(grupo)
    return grupos


def _planejar_composicao(qtd_paisagens, qtd_retratos):
    """Minimiza fotos avulsas e, em empate, a quantidade de páginas."""
    @lru_cache(maxsize=None)
    def resolver(paisagens, retratos):
        if paisagens == 0 and retratos == 0:
            return (0, 0, ())  # avulsas, páginas, composição

        opcoes = []
        for indice, (usa_paisagens, usa_retratos) in enumerate(_TEMPLATES):
            if usa_paisagens <= paisagens and usa_retratos <= retratos:
                avulsas, paginas, composicao = resolver(
                    paisagens - usa_paisagens, retratos - usa_retratos
                )
                opcoes.append((
                    avulsas, paginas + 1,
                    composicao + ((usa_paisagens, usa_retratos),), indice,
                ))

        # Resto impossível de encaixar: isola a foto, sem criar template
        # incompatível com a orientação dela.
        if paisagens:
            avulsas, paginas, composicao = resolver(paisagens - 1, retratos)
            opcoes.append((
                avulsas + 1, paginas + 1, composicao + ((1, 0),), len(_TEMPLATES),
            ))
        if retratos:
            avulsas, paginas, composicao = resolver(paisagens, retratos - 1)
            opcoes.append((
                avulsas + 1, paginas + 1, composicao + ((0, 1),), len(_TEMPLATES) + 1,
            ))

        melhor = min(opcoes, key=lambda opcao: (opcao[0], opcao[1], opcao[3]))
        return melhor[:3]

    return list(resolver(qtd_paisagens, qtd_retratos)[2])
