import os
import re

import tiktoken
from langchain_text_splitters import TokenTextSplitter

from dtos.politicas_dto import NAMESPACE_ESTRUCTURAL, PolicyChunk
from integracion.upstash_integracion import upsert_chunks

_ENCODING_NAME = "cl100k_base"
_ENCODING = tiktoken.get_encoding(_ENCODING_NAME)
_PATRON_HEADING_NIVEL_2 = re.compile(r"^##\s+(?!#)(.+?)\s*$")
_PATRON_HEADING_NIVEL_3 = re.compile(r"^###\s+(?!#)(.+?)\s*$")
_PATRON_HEADING_NIVEL_2_O_3 = re.compile(r"^#{2,3}\s+(?!#)(.+?)\s*$")
_PATRON_HEADING_LIMITE = re.compile(r"^#{1,3}\s+(?!#)")
_PATRON_SECCION_NUMERADA = re.compile(r"^(\d+(?:\.\d+)*)\s+(.+)$")
_PATRON_SECCION_NIVEL_2 = re.compile(r"^#{2}\s+SECCIÓN\s+\d", re.IGNORECASE)

_RUTA_POLITICAS = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "politicas_ecommerce_integral.md"
)


def indexar_politicas_estructural(ruta_markdown: str = _RUTA_POLITICAS) -> int:
    with open(ruta_markdown, encoding="utf-8") as archivo:
        markdown = archivo.read()
    chunks = chunker_estructural(markdown)
    return indexar_chunks(chunks, namespace=NAMESPACE_ESTRUCTURAL)


def indexar_chunks(chunks: list[PolicyChunk], namespace: str) -> int:
    if not chunks:
        return 0
    upsert_chunks(chunks, namespace=namespace)
    return len(chunks)


def chunker_estructural(markdown: str) -> list[PolicyChunk]:
    lineas = markdown.splitlines()
    indices_h2 = [indice for indice, linea in enumerate(lineas) if _PATRON_HEADING_NIVEL_2.match(linea)]
    indices_h3 = [indice for indice, linea in enumerate(lineas) if _PATRON_HEADING_NIVEL_3.match(linea)]
    indices_h2_sin_hijos = [
        indice
        for indice in indices_h2
        if _PATRON_SECCION_NIVEL_2.match(lineas[indice])
        and not _tiene_hijo_nivel_3(indice, indices_h2, indices_h3, len(lineas))
    ]
    indices_encabezado = sorted(indices_h3 + indices_h2_sin_hijos)
    return [_chunk_desde_encabezado(lineas, indice) for indice in indices_encabezado]


def chunker_tamano_fijo(texto: str, tamano_tokens: int, overlap_pct: float) -> list[PolicyChunk]:
    overlap_tokens = round(tamano_tokens * overlap_pct)
    splitter = TokenTextSplitter(
        encoding_name=_ENCODING_NAME,
        chunk_size=tamano_tokens,
        chunk_overlap=overlap_tokens,
    )
    fragmentos = splitter.split_text(texto)
    return [
        _chunk_desde_fragmento(fragmento, tamano_tokens, overlap_pct, indice)
        for indice, fragmento in enumerate(fragmentos)
    ]


def _chunk_desde_encabezado(lineas: list[str], indice_encabezado: int) -> PolicyChunk:
    encabezado = _PATRON_HEADING_NIVEL_2_O_3.match(lineas[indice_encabezado]).group(1)  # type: ignore[union-attr]
    indice_fin = _encontrar_limite_de_seccion(lineas, indice_encabezado + 1)
    cuerpo = "\n".join(lineas[indice_encabezado + 1 : indice_fin]).strip()
    texto_chunk = f"{encabezado}\n{cuerpo}".strip()
    seccion, titulo = _parsear_seccion_y_titulo(encabezado)
    return PolicyChunk(
        id=seccion,
        texto=texto_chunk,
        seccion=seccion,
        titulo=titulo,
        estrategia="estructural",
        parametros=None,
        num_tokens=_contar_tokens(texto_chunk),
    )


def _encontrar_limite_de_seccion(lineas: list[str], desde: int) -> int:
    for indice in range(desde, len(lineas)):
        if _PATRON_HEADING_LIMITE.match(lineas[indice]):
            return indice
    return len(lineas)


def _tiene_hijo_nivel_3(
    indice_h2: int, indices_h2: list[int], indices_h3: list[int], total_lineas: int
) -> bool:
    siguientes_h2 = [indice for indice in indices_h2 if indice > indice_h2]
    limite = min(siguientes_h2) if siguientes_h2 else total_lineas
    return any(indice_h2 < indice < limite for indice in indices_h3)


def _parsear_seccion_y_titulo(encabezado: str) -> tuple[str, str]:
    coincidencia = _PATRON_SECCION_NUMERADA.match(encabezado)
    if coincidencia is None:
        return encabezado, encabezado
    return coincidencia.group(1), coincidencia.group(2).strip()


def _chunk_desde_fragmento(
    fragmento: str, tamano_tokens: int, overlap_pct: float, indice: int
) -> PolicyChunk:
    overlap_pct_label = round(overlap_pct * 100)
    return PolicyChunk(
        id=f"{tamano_tokens}_{overlap_pct_label}_{indice}",
        texto=fragmento,
        seccion=None,
        titulo=None,
        estrategia="tamano_fijo",
        parametros={"tamano_tokens": tamano_tokens, "overlap_pct": overlap_pct},
        num_tokens=_contar_tokens(fragmento),
    )


def _contar_tokens(texto: str) -> int:
    return len(_ENCODING.encode(texto))
