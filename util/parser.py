"""
Funções de limpeza/formatação de texto: nomes de pastas viram títulos
legíveis, e nomes de arquivo viram legendas de foto.
"""

import re

_ACENTOS = {
    "Conteiner": "Contêiner",
    "Organizacao": "Organização",
    "Seguranca": "Segurança",
    "Zeladoria": "Zeladoria",
}

# Siglas curtas de Contêiner/Fila/Rack (ex: "C1", "F1", "R1") — removidas
# da legenda porque o tópico da página já mostra essa referência.
# Nomes extensos como "Fila01", "Rack01", "Corredor" NÃO são siglas e
# continuam aparecendo normalmente.
_PADRAO_SIGLA = re.compile(r"^[CFR]\d+$", re.IGNORECASE)
_PADRAO_REFERENCIA = re.compile(r"(?:^|[-_\s])([CFR])0*(\d+)(?=$|[-_\s])", re.IGNORECASE)


def _categoria_com_referencias(categoria: str) -> bool:
    categoria_normalizada = re.sub(r"[^A-Z]", "", categoria.upper())
    return categoria_normalizada in {"INFRA", "ZELADORIA"}


def _referencias_estrutura(nome: str) -> list[str]:
    """Extrai Cxx/Fxx/Rxx, preservando a ordem e removendo repetições."""
    nomes = {"C": "Cont\u00eainer", "F": "Fila", "R": "Rack"}
    referencias = []
    for sigla, numero in _PADRAO_REFERENCIA.findall(nome):
        referencia = f"{nomes[sigla.upper()]} {int(numero):02d}"
        if referencia not in referencias:
            referencias.append(referencia)
    return referencias


def titulo_amigavel(nome_pasta: str) -> str:
    """
    'CONTEINER 01'   -> 'Contêiner 01'
    'AMBIENTE EXTERNO' -> 'Ambiente Externo'
    'RACK 04'        -> 'Rack 04'
    """
    nome = nome_pasta.strip()
    palavras = []

    for palavra in nome.split():
        if palavra.isdigit():
            palavras.append(palavra)
        else:
            palavras.append(palavra.capitalize())

    texto = " ".join(palavras)

    for errado, certo in _ACENTOS.items():
        texto = texto.replace(errado, certo)

    return texto


def legenda_da_foto(caminho_arquivo, prefixo_site: str = "", categoria: str = "") -> str:
    """
    'HUB_SEA-C2-F1-R1-RFGW-NOW.jpg' (prefixo 'HUB_SEA')
        -> 'RFGW NOW'          (C2/F1/R1 removidos: são só siglas)
    'HUB_SEA-C2-F1-Rack01-Front.jpg'
        -> 'Rack01 Front'      (Rack01 é nome extenso, mantido)
    'HUB_SEA-C1-Corredor.jpg'
        -> 'Corredor'
    """
    nome = caminho_arquivo.stem
    referencias = _referencias_estrutura(nome) if _categoria_com_referencias(categoria) else []

    if prefixo_site and nome.upper().startswith(prefixo_site.upper()):
        nome = nome[len(prefixo_site):]

    nome = nome.strip("-_ ")

    tokens = re.split(r"[-_\s]+", nome)
    tokens_uteis = [t for t in tokens if t and not _PADRAO_SIGLA.match(t)]

    legenda = " ".join(tokens_uteis)
    legenda = legenda.strip() or caminho_arquivo.stem
    return " · ".join([*referencias, legenda]) if referencias else legenda
