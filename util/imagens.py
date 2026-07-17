"""
Utilitários de imagem:
  - corrige a orientação EXIF de verdade (fotos de celular vêm com
    metadado de rotação que, se ignorado, faz a imagem entrar
    torta no PDF);
  - identifica a orientação real da foto — primeiro tenta pelo padrão
    do nome do arquivo (mais confiável para fotos de Rack/Fila, que
    são sempre verticais, exceto fotos de equipamento específico tipo
    "C2-F1-R1-RFGW-NOW", que são horizontais); se o nome não dá
    nenhuma pista, cai para o tamanho real do pixel;
  - redimensiona a foto para a resolução que ela realmente vai
    ocupar no PDF antes de embutir. Sem isso, fotos de câmera/celular
    (várias MB, 12+ megapixels cada) deixam o PDF gigante quando o
    relatório tem centenas de fotos — foi isso que causou o erro
    "No space left on device".
"""

import re
from io import BytesIO

from PIL import Image, ImageOps

DPI_ALVO = 150          # suficiente para impressão/leitura em tela, bem menor que o original
QUALIDADE_JPEG = 82

# Fotos de equipamento específico dentro de um rack, ex: "C2-F1-R1-RFGW-NOW.jpg"
# (Contêiner-Fila-Rack em forma curta, seguido do código do equipamento) — essas
# são tiradas na horizontal, mesmo estando dentro de uma pasta de Rack/Fila.
_PADRAO_EQUIPAMENTO = re.compile(r"C\d+[-_]?F\d+[-_]?R\d+[-_]", re.IGNORECASE)

# "Rack01", "Fila02", "Corredor..." escritos por extenso no nome do
# arquivo — fotos do rack/fila/corredor inteiro, sempre tiradas na
# vertical. O \b (borda de palavra) é essencial: sem ele, "EntreFila01"
# (uma foto geral do corredor entre filas, paisagem) seria confundida
# com "Fila01" só por conter esse trecho no meio da palavra.
_PADRAO_RACK_FILA = re.compile(r"\b(RACK\d+|FILA\d+|CORREDOR)", re.IGNORECASE)


def orientacao_por_nome(nome_arquivo: str):
    """
    Tenta decidir a orientação pelo padrão do nome do arquivo.
    Retorna 'retrato', 'paisagem' ou None (sem regra aplicável — usa o pixel real).
    """
    nome = nome_arquivo.upper()

    if _PADRAO_EQUIPAMENTO.search(nome):
        return "paisagem"

    if _PADRAO_RACK_FILA.search(nome):
        return "retrato"

    return None


def parametros_qualidade(nome_arquivo: str):
    """
    Fotos de equipamento e de rack/fila costumam precisar de mais
    nitidez (às vezes é preciso ler etiqueta, porta, status de LED
    etc.) — usam DPI e qualidade JPEG mais altos que fotos gerais
    (fachada, pátio, guarita...).
    """
    nome = nome_arquivo.upper()

    if _PADRAO_EQUIPAMENTO.search(nome):
        return 220, 92   # foto de equipamento específico — precisa de detalhe/etiqueta legível

    if _PADRAO_RACK_FILA.search(nome):
        return 190, 90   # foto do rack/fila inteiro

    return DPI_ALVO, QUALIDADE_JPEG   # fotos gerais


def dimensoes_ajustadas(caminho_imagem, largura_max, altura_max):
    """
    Retorna (largura, altura) — nas mesmas unidades de largura_max/altura_max —
    já ajustadas para caber nesse espaço, preservando a proporção real
    da imagem (já considerando a rotação EXIF).
    """
    largura_original, altura_original = _tamanho_real(caminho_imagem)

    escala = min(largura_max / largura_original, altura_max / altura_original)

    return largura_original * escala, altura_original * escala


def preparar_para_pdf(caminho_imagem, largura_pt, altura_pt, dpi=None, qualidade=None):
    """
    Abre a imagem, corrige a orientação EXIF, reduz para a resolução
    necessária para ocupar (largura_pt x altura_pt) no PDF, e devolve
    um buffer JPEG em memória pronto para o reportlab.
    Nunca aumenta a imagem — só reduz.

    Se dpi/qualidade não forem informados, são escolhidos automaticamente
    pelo tipo de foto (equipamento e rack/fila recebem mais nitidez).
    """
    if dpi is None or qualidade is None:
        dpi_auto, qualidade_auto = parametros_qualidade(caminho_imagem.name)
        dpi = dpi if dpi is not None else dpi_auto
        qualidade = qualidade if qualidade is not None else qualidade_auto

    largura_alvo_px = max(int(largura_pt / 72 * dpi), 1)
    altura_alvo_px = max(int(altura_pt / 72 * dpi), 1)

    with Image.open(caminho_imagem) as img:
        img = ImageOps.exif_transpose(img)
        img = _para_rgb(img)

        img.thumbnail((largura_alvo_px, altura_alvo_px), Image.LANCZOS)

        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=qualidade, optimize=True)

    buffer.seek(0)
    return buffer


def _tamanho_real(caminho_imagem):
    """Tamanho da imagem já considerando a rotação EXIF."""
    with Image.open(caminho_imagem) as img:
        img = ImageOps.exif_transpose(img)
        return img.size


def orientacao(caminho_imagem):
    """
    Retorna 'retrato' ou 'paisagem' pelo tamanho real do pixel, já
    considerando a rotação EXIF. O nome do arquivo não é usado para
    evitar que uma convenção de nomenclatura altere o template da foto.
    """
    largura, altura = _tamanho_real(caminho_imagem)
    return "retrato" if altura > largura else "paisagem"


def _para_rgb(img):
    """Garante modo RGB (sem transparência) para poder salvar como JPEG."""
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        fundo = Image.new("RGB", img.size, (255, 255, 255))
        img_rgba = img.convert("RGBA")
        fundo.paste(img_rgba, mask=img_rgba.split()[-1])
        return fundo

    if img.mode != "RGB":
        return img.convert("RGB")

    return img
