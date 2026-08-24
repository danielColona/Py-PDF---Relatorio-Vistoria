"""
Gera o Book completo do site e os 3 books derivados (Zeladoria,
Organização, Infra), reaproveitando Capa + Sumário + a(s) seção(ões)
correspondente(s) diretamente do PDF completo já gerado — mesma
estrutura usada nos books anteriores (ex: JUN26).
"""

from datetime import date

from pypdf import PdfReader, PdfWriter
from PIL import Image as PILImage

from util.config import Configuracao
from modelos.relatorio import RelatorioPDF

_MESES = {
    1: "JAN", 2: "FEV", 3: "MAR", 4: "ABR", 5: "MAI", 6: "JUN",
    7: "JUL", 8: "AGO", 9: "SET", 10: "OUT", 11: "NOV", 12: "DEZ",
}

# Books secundários (Zeladoria/Organização/Infra) não podem passar disso.
# O Book completo nunca é comprimido.
_LIMITE_MB_SECUNDARIOS = 10

# Níveis de recompressão de imagem tentados em ordem, do mais leve ao
# mais agressivo, até o arquivo caber no limite.
_NIVEIS_COMPRESSAO = [(0.85, 75), (0.75, 65), (0.65, 55), (0.55, 45), (0.45, 35)]


def _tamanho_mb(caminho):
    return caminho.stat().st_size / (1024 * 1024)


def _comprimir_pdf(caminho_original, caminho_comprimido, limite_mb=_LIMITE_MB_SECUNDARIOS):
    """Recomprime as imagens embutidas no PDF (reduz resolução/qualidade
    JPEG) até o arquivo ficar abaixo do limite, tentando níveis cada vez
    mais agressivos. Não altera o arquivo original."""
    for escala, qualidade in _NIVEIS_COMPRESSAO:
        writer = PdfWriter(clone_from=str(caminho_original))
        for pagina in writer.pages:
            for imagem in pagina.images:
                pil_img = imagem.image
                nova_largura = max(int(pil_img.width * escala), 1)
                nova_altura = max(int(pil_img.height * escala), 1)
                redimensionada = pil_img.resize(
                    (nova_largura, nova_altura), PILImage.LANCZOS
                )
                if redimensionada.mode != "RGB":
                    redimensionada = redimensionada.convert("RGB")
                imagem.replace(redimensionada, quality=qualidade)

        writer.compress_identical_objects()
        with open(caminho_comprimido, "wb") as f:
            writer.write(f)

        tamanho = _tamanho_mb(caminho_comprimido)
        print(f"    tentativa escala={escala} qualidade={qualidade} -> {tamanho:.1f} MB")
        if tamanho <= limite_mb:
            return True

    return False


def _mes_ano():
    hoje = date.today()
    return f"{_MESES[hoje.month]}{hoje.year % 100:02d}"


def _pagina_do_marcador(reader, titulo):
    for item in reader.outline:
        if isinstance(item, list):
            continue
        if item.title == titulo:
            return reader.get_destination_page_number(item)
    raise ValueError(f"Marcador '{titulo}' não encontrado no PDF completo.")


def _extrair_livro(reader, caminho_saida, inicio_conteudo, fim_conteudo):
    """Monta um book derivado: Capa + Sumário (páginas 0-1, iguais ao
    completo) + o intervalo [inicio_conteudo, fim_conteudo) de conteúdo
    (contra capa do grupo + seções).

    As páginas são copiadas numa única chamada a append() (lista combinada,
    não dois append() separados) para que o pypdf remapeie corretamente os
    links internos entre elas — ex: o "Voltar ao Sumário" do cabeçalho e as
    entradas do Sumário que apontam pra seção presente neste book. Links
    para seções que ficaram de fora (não incluídas no intervalo) continuam
    inertes, o que é esperado."""
    paginas = [0, 1] + list(range(inicio_conteudo, fim_conteudo))
    writer = PdfWriter()
    writer.append(reader, pages=paginas)
    try:
        with open(caminho_saida, "wb") as f:
            writer.write(f)
    except PermissionError as erro:
        raise PermissionError(
            f"Não foi possível gravar '{caminho_saida}'. "
            "Feche o arquivo (provavelmente está aberto em um leitor de PDF) e tente novamente."
        ) from erro

    tamanho = _tamanho_mb(caminho_saida)
    print(f"Gerado: {caminho_saida} ({len(writer.pages)} páginas, {tamanho:.1f} MB)")

    if tamanho > _LIMITE_MB_SECUNDARIOS:
        caminho_comprimido = caminho_saida.with_name(
            caminho_saida.stem + "_compressed" + caminho_saida.suffix
        )
        print(f"  acima de {_LIMITE_MB_SECUNDARIOS} MB — gerando versão comprimida...")
        ok = _comprimir_pdf(caminho_saida, caminho_comprimido)
        tamanho_final = _tamanho_mb(caminho_comprimido)
        if ok:
            print(f"  Gerado: {caminho_comprimido} ({tamanho_final:.1f} MB)")
        else:
            print(
                f"  [aviso] Não foi possível comprimir {caminho_comprimido.name} "
                f"abaixo de {_LIMITE_MB_SECUNDARIOS} MB (ficou em {tamanho_final:.1f} MB "
                "no nível mais agressivo)."
            )


def main():
    config = Configuracao()
    sufixo = _mes_ano()
    prefixo_site = config.site.replace(" ", "_")

    caminho_completo = config.pasta_saida / f"Book_Vistoria-{sufixo}-{prefixo_site}.pdf"

    print("=" * 60)
    print("Gerando o Book completo...")
    print("=" * 60)
    RelatorioPDF(config).gerar(caminho_saida=caminho_completo)

    print()
    print("Separando os books por seção...")
    reader = PdfReader(str(caminho_completo))

    p_seguranca = _pagina_do_marcador(reader, "Segurança")
    p_organizacao = _pagina_do_marcador(reader, "Organização")
    p_infra = _pagina_do_marcador(reader, "Infra")
    total_paginas = len(reader.pages)

    contracapa_seguranca = p_seguranca - 1
    contracapa_organizacao = p_organizacao - 1
    contracapa_infra = p_infra - 1

    _extrair_livro(
        reader,
        config.pasta_saida / f"Book_Zeladoria-Vistoria-{sufixo}-{prefixo_site}.pdf",
        contracapa_seguranca, contracapa_organizacao,
    )
    _extrair_livro(
        reader,
        config.pasta_saida / f"Book_Organizacao-Vistoria-{sufixo}-{prefixo_site}.pdf",
        contracapa_organizacao, contracapa_infra,
    )
    _extrair_livro(
        reader,
        config.pasta_saida / f"Book_Infra-Vistoria-{sufixo}-{prefixo_site}.pdf",
        contracapa_infra, total_paginas,
    )

    print()
    print("=" * 60)
    print("Todos os books foram gerados em:", config.pasta_saida.resolve())
    print("=" * 60)


if __name__ == "__main__":
    main()
