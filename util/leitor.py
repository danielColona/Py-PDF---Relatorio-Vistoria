"""
Varredura recursiva da pasta do site.

Qualquer pasta que contenha fotos (direta ou indiretamente, em subpastas)
vira uma Secao do relatório. Pastas totalmente vazias são ignoradas
automaticamente — não é preciso configurar nada quando uma pasta como
INFRA/ARCON ainda não tem fotos.

A ordem de exibição segue uma prioridade fixa (SEGURANÇA, ZELADORIA,
ORGANIZAÇÃO, INFRA, e sub-ordens conhecidas dentro de cada uma);
pastas não previstas na lista entram depois, em ordem alfabética.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

EXTENSOES_VALIDAS = {".jpg", ".jpeg", ".png", ".bmp"}

_ORDEM_PERSONALIZADA = {
    # Categorias de topo
    "SEGURANCA": 0,
    "ZELADORIA": 1,
    "ORGANIZACAO": 2,
    "INFRA": 3,
    # Dentro de SEGURANCA
    "FACHADA": 0,
    "PORTA ACESSO": 1,
    # Dentro de ZELADORIA
    "AMBIENTE EXTERNO": 0,
    "AMBIENTE INTERNO": 1,
    # Dentro de INFRA
    "ARCON": 0,
    "UPS": 1,
    "GERADOR": 2,
    "RETIFICADOR": 3,
    "QUADROS": 4,
    "SDAI": 5,
}


def _normalizar(nome: str) -> str:
    """Remove acentos e caixa para comparar nomes de pasta com segurança."""
    nfkd = unicodedata.normalize("NFKD", nome.upper())
    return "".join(c for c in nfkd if not unicodedata.combining(c)).strip()


def _chave_ordenacao(nome_pasta: str):
    prioridade = _ORDEM_PERSONALIZADA.get(_normalizar(nome_pasta), 999)
    return (prioridade, nome_pasta)


_TOKENS_IGNORADOS_NA_FOTO = {
    "HUB", "SEA", "INFRA", "SEG", "SEGURANCA", "ZELADORIA", "ORGANIZACAO",
    "SDAI",
}
_CODIGO_ESTRUTURA = re.compile(r"^[CFR]\d+$", re.IGNORECASE)


def _partes_naturais(texto: str):
    """Permite que 2 venha antes de 10, sem depender de zeros à esquerda."""
    return tuple(
        int(parte) if parte.isdigit() else parte
        for parte in re.split(r"(\d+)", _normalizar(texto))
    )


def _chave_ordenacao_foto(caminho: Path):
    """Agrupa fotos pelo nome principal e ordena cada grupo naturalmente.

    Prefixos do site/categoria e códigos estruturais (Cxx/Fxx/Rxx) não são
    usados como grupo. Assim, fotos PLC ficam juntas em SDAI, Guarita fica
    junto em Zeladoria e sequências como Patio2/Patio10 ficam na ordem humana.
    """
    tokens = [t for t in re.split(r"[-_\s]+", caminho.stem) if t]
    relevantes = [
        token for token in tokens
        if _normalizar(token) not in _TOKENS_IGNORADOS_NA_FOTO
        and not _CODIGO_ESTRUTURA.match(token)
    ]
    principal = relevantes[0] if relevantes else caminho.stem
    grupo = re.sub(r"\d+$", "", _normalizar(principal)) or _normalizar(principal)
    return (grupo, _partes_naturais(" ".join(relevantes)), _partes_naturais(caminho.name))


@dataclass
class Secao:
    nome: str
    caminho: Path
    nivel: int
    imagens: list = field(default_factory=list)
    subsecoes: list = field(default_factory=list)

    @property
    def tem_conteudo(self):
        if self.imagens:
            return True
        return any(sub.tem_conteudo for sub in self.subsecoes)

    def total_fotos(self):
        total = len(self.imagens)
        for sub in self.subsecoes:
            total += sub.total_fotos()
        return total


def ler_estrutura(pasta_raiz: Path, nivel: int = 1):
    """
    Varre pasta_raiz e retorna uma lista de Secao — uma para cada
    subpasta que contém fotos (própria ou herdada de subpastas).
    """
    secoes = []

    if not pasta_raiz.exists():
        return secoes

    for item in sorted(pasta_raiz.iterdir(), key=lambda p: _chave_ordenacao(p.name)):
        if not item.is_dir():
            continue

        secao = Secao(nome=item.name, caminho=item, nivel=nivel)

        secao.imagens = sorted(
            (
                f for f in item.iterdir()
                if f.is_file() and f.suffix.lower() in EXTENSOES_VALIDAS
            ),
            key=_chave_ordenacao_foto,
        )

        secao.subsecoes = ler_estrutura(item, nivel + 1)

        if secao.tem_conteudo:
            secoes.append(secao)

    return secoes
