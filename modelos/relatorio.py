"""
Classe principal do relatório: orquestra capa, sumário, marcadores
(bookmarks) e páginas de fotos, varrendo a pasta do site.
"""

from reportlab.lib.styles import ParagraphStyle
import re
import unicodedata
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    NextPageTemplate,
    Paragraph,
    Spacer,
    PageBreak,
)

from util.leitor import ler_estrutura
from util.parser import titulo_amigavel
from util.progresso import Progresso
from . import layout
from .capa import desenhar_capa, desenhar_contracapa
from .sumario import criar_sumario
from .bookmarks import registrar_marcador
from .paginas import construir_flowables, estilos_secao


def _slug(texto):
    """Normaliza um nome de categoria pra usar como chave de marcador
    (ex: 'Segurança' -> 'seguranca'), previsível independente de acentos."""
    nfkd = unicodedata.normalize("NFKD", texto.upper())
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]+", "_", sem_acento).strip("_").lower()


# Agrupamento das categorias de topo para as páginas de contra capa —
# cada grupo vira uma divisória antes do respectivo conteúdo.
# INFRA fica em um grupo próprio, sempre por último.
GRUPOS_CONTRACAPA = [
    ["SEGURANCA", "ZELADORIA"],
    ["ORGANIZACAO"],
    ["INFRA"],
]


_ESTILO_TITULO_SUMARIO = ParagraphStyle(
    "TituloSumario", fontName=layout.FONTE_NIVEL1,
    fontSize=layout.TAMANHO_NIVEL1, textColor=layout.COR_TITULO,
    spaceAfter=8,
)


_PADRAO_ESTILO_SECAO = re.compile(r"^SecaoNivel([1-4])$")


class _DocTemplate(BaseDocTemplate):
    """
    Subclasse necessária para registrar marcadores (bookmarks) e
    entradas do sumário automaticamente sempre que um título de
    seção (estilo 'SecaoNivelN') é desenhado no PDF.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._contador_marcador = 0

    def build(self, *args, **kwargs):
        # multiBuild() chama build() várias vezes até o sumário estabilizar;
        # o contador precisa reiniciar a cada passada, senão as chaves dos
        # marcadores mudam de uma passada para a outra e o sumário nunca
        # converge.
        self._contador_marcador = 0
        self._numero_passada = getattr(self, "_numero_passada", 0) + 1
        print(f"  passada {self._numero_passada} (ajustando sumário/páginas)...")
        return super().build(*args, **kwargs)

    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return

        estilo = flowable.style.name

        if estilo == "TituloSumario":
            # Marca esta página como destino do link "Voltar ao Sumário"
            # que aparece no cabeçalho de todas as outras páginas.
            self.canv.bookmarkPage("toc")
            return

        correspondencia = _PADRAO_ESTILO_SECAO.match(estilo)
        if not correspondencia:
            # Não é um título de seção "de verdade" (pode ser uma repetição
            # de ancestral, ex: 'SecaoNivel2Repeticao') — não registra de novo.
            return

        nivel_secao = int(correspondencia.group(1))      # 1..4
        nivel_outline = nivel_secao - 1    # 0..3 (bookmarks aceitam níveis mais fundos)

        texto = flowable.getPlainText()

        if nivel_secao == 1:
            # Chave previsível (ex: 'cat_seguranca'), pra poder ser linkada
            # pela contra capa antes mesmo dessa página existir no fluxo.
            chave = f"cat_{_slug(texto)}"
        else:
            self._contador_marcador += 1
            chave = f"sec_{self._contador_marcador}"

        registrar_marcador(self.canv, chave, texto, nivel_outline)

        if nivel_outline < layout.PROFUNDIDADE_MAXIMA_SUMARIO:
            self.notify("TOCEntry", (nivel_outline, texto, self.page, chave))


class RelatorioPDF:

    def __init__(self, config):
        self.config = config
        config.pasta_saida.mkdir(exist_ok=True)

    # -----------------------------------------------------
    def _desenhar_cabecalho_rodape(self, canvas, doc):
        canvas.saveState()
        largura, altura = layout.PAGINA

        # Cabeçalho — empresa/site à esquerda
        canvas.setFont(layout.FONTE_CABECALHO, layout.TAMANHO_CABECALHO)
        canvas.setFillColor(layout.COR_TEXTO_CLARO)
        canvas.drawString(
            layout.MARGEM_ESQUERDA, altura - 14,
            f"{self.config.empresa}  |  {self.config.site}",
        )

        # Cabeçalho — link "Voltar ao Sumário" à direita, clicável
        texto_link = "↑ Voltar ao Sumário"
        canvas.setFont(layout.FONTE_CABECALHO, layout.TAMANHO_CABECALHO)
        canvas.setFillColor(layout.COR_LINHA)
        largura_texto = canvas.stringWidth(
            texto_link, layout.FONTE_CABECALHO, layout.TAMANHO_CABECALHO
        )
        x_link = largura - layout.MARGEM_DIREITA - largura_texto
        y_link = altura - 14
        canvas.drawString(x_link, y_link, texto_link)
        canvas.linkRect(
            "", "toc",
            (x_link - 3, y_link - 3, x_link + largura_texto + 3, y_link + layout.TAMANHO_CABECALHO + 3),
            relative=0, thickness=0,
        )

        canvas.setStrokeColor(layout.COR_LINHA)
        canvas.setLineWidth(0.6)
        canvas.line(
            layout.MARGEM_ESQUERDA, altura - 18,
            largura - layout.MARGEM_DIREITA, altura - 18,
        )

        # Rodapé
        canvas.setFont(layout.FONTE_RODAPE, layout.TAMANHO_RODAPE)
        canvas.drawString(layout.MARGEM_ESQUERDA, 12, self.config.titulo)
        canvas.drawRightString(
            largura - layout.MARGEM_DIREITA, 12,
            f"Página {canvas.getPageNumber()}",
        )

        canvas.restoreState()

    # -----------------------------------------------------
    def gerar(self, caminho_saida=None):

        caminho_saida = caminho_saida or self.config.arquivo_pdf

        print(f"Lendo pasta do site: {self.config.pasta_site}")
        secoes = ler_estrutura(self.config.pasta_site)

        if not secoes:
            print()
            print("!" * 60)
            print(f"Nenhuma foto encontrada em: {self.config.pasta_site}")
            print("Verifique o caminho 'pasta_site' no config.json.")
            print("!" * 60)
            return

        total_fotos = sum(s.total_fotos() for s in secoes)
        print(f"{len(secoes)} seção(ões) e {total_fotos} foto(s) encontradas.")
        print()

        doc = _DocTemplate(
            str(caminho_saida),
            pagesize=layout.PAGINA,
            leftMargin=layout.MARGEM_ESQUERDA,
            rightMargin=layout.MARGEM_DIREITA,
            topMargin=layout.MARGEM_SUPERIOR,
            bottomMargin=layout.MARGEM_INFERIOR,
        )

        frame_capa = Frame(
            doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="capa",
        )
        frame_conteudo = Frame(
            doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="conteudo",
        )

        # Sumário em 2 colunas, lado a lado, para caber tudo numa página só
        gap_colunas = 14
        largura_coluna = (doc.width - gap_colunas) / 2
        frame_sumario_esq = Frame(
            doc.leftMargin, doc.bottomMargin, largura_coluna, doc.height,
            id="sumario_esq", leftPadding=0, rightPadding=8,
        )
        frame_sumario_dir = Frame(
            doc.leftMargin + largura_coluna + gap_colunas, doc.bottomMargin,
            largura_coluna, doc.height,
            id="sumario_dir", leftPadding=8, rightPadding=0,
        )

        template_capa = PageTemplate(
            id="capa",
            frames=[frame_capa],
            onPage=lambda c, d: desenhar_capa(c, self.config),
        )
        template_conteudo = PageTemplate(
            id="conteudo",
            frames=[frame_conteudo],
            onPage=self._desenhar_cabecalho_rodape,
        )
        template_sumario = PageTemplate(
            id="sumario",
            frames=[frame_sumario_esq, frame_sumario_dir],
            onPage=self._desenhar_cabecalho_rodape,
        )

        # 'capa' é o primeiro template da lista => usado na página 1
        doc.addPageTemplates([template_capa, template_conteudo, template_sumario])

        # ---- Agrupa as categorias de topo para as contra capas ----
        secoes_por_slug = {_slug(s.nome): s for s in secoes}
        usados = set()
        grupos_finais = []   # lista de (membros, id_template_contracapa_ou_None)

        for indice, grupo_nomes in enumerate(GRUPOS_CONTRACAPA):
            membros = [
                secoes_por_slug[_slug(nome)]
                for nome in grupo_nomes
                if _slug(nome) in secoes_por_slug
            ]
            if membros:
                grupos_finais.append((membros, f"contracapa_{indice}"))
                usados.update(id(m) for m in membros)

        # Categorias que não se encaixaram em nenhum grupo conhecido (ex:
        # uma pasta nova no futuro) entram no final, sem contra capa própria.
        extras = [s for s in secoes if id(s) not in usados]
        if extras:
            grupos_finais.append((extras, None))

        # Cria um PageTemplate de contra capa para cada grupo que tiver um.
        frame_contracapa = Frame(
            doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="contracapa",
        )
        for membros, id_template in grupos_finais:
            if id_template is None:
                continue
            itens = [(titulo_amigavel(m.nome), f"cat_{_slug(m.nome)}") for m in membros]
            template_contracapa = PageTemplate(
                id=id_template,
                frames=[frame_contracapa],
                onPage=(lambda c, d, itens=itens: desenhar_contracapa(c, self.config, itens)),
            )
            doc.addPageTemplates([template_contracapa])

        # ---- Monta o roteiro do documento ----
        elementos = []

        elementos.append(NextPageTemplate("sumario"))
        elementos.append(PageBreak())  # fecha a capa, abre o sumário (2 colunas)

        elementos.append(Paragraph("Sumário", _ESTILO_TITULO_SUMARIO))
        elementos.append(Spacer(1, 4))
        elementos.append(criar_sumario())

        progresso = Progresso(total_fotos, rotulo="Processando fotos")

        for membros, id_template in grupos_finais:
            if id_template is not None:
                elementos.append(NextPageTemplate(id_template))
                elementos.append(PageBreak())   # abre a contra capa
                elementos.append(NextPageTemplate("conteudo"))
                elementos.append(PageBreak())   # fecha a contra capa, abre o conteúdo
            else:
                elementos.append(NextPageTemplate("conteudo"))
                elementos.append(PageBreak())

            elementos.extend(
                construir_flowables(
                    membros, self.config, doc.width, doc.height, progresso=progresso
                )
            )

        progresso.finalizar()

        print("Gerando o arquivo PDF (isso pode levar alguns segundos)...")
        doc.multiBuild(elementos)

        total_fotos = sum(s.total_fotos() for s in secoes)

        print()
        print("=" * 60)
        print("PDF gerado com sucesso!")
        print(f"Seções encontradas: {len(secoes)}")
        print(f"Total de fotos:     {total_fotos}")
        print(f"Arquivo:            {caminho_saida}")
        print("=" * 60)