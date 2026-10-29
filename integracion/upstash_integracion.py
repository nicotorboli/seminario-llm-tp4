from langchain_core.tools import tool
from upstash_vector import Vector

from dtos.politicas_dto import NAMESPACE_ESTRUCTURAL, PolicyChunk
from settings import cliente_upstash

_DESCRIPCION_TOOL = (
    "Busca, en el manual de políticas vigente de la empresa, los fragmentos más relevantes "
    "para una consulta sobre envíos, garantías, facturación o devoluciones. Usala antes de "
    "decidir qué política aplica a un reclamo; no asumas ninguna política sin buscarla primero."
)
_MOTIVO_SIN_RESULTADOS = "No se encontraron políticas suficientemente relevantes para esta consulta."
_MOTIVO_CONSULTA_VACIA = "La consulta no puede estar vacía."


@tool(description=_DESCRIPCION_TOOL)
def buscar_politica(consulta: str, k: int = 3) -> dict:
    return buscar_politica_impl(consulta, k)


def buscar_politica_impl(consulta: str, k: int = 3) -> dict:
    if not consulta.strip():
        return {"resultados": [], "motivo": _MOTIVO_CONSULTA_VACIA}
    try:
        chunks = query_chunks(consulta, k)
    except Exception:
        return {"resultados": [], "motivo": _MOTIVO_SIN_RESULTADOS}
    if not chunks:
        return {"resultados": [], "motivo": _MOTIVO_SIN_RESULTADOS}
    return {"resultados": [_chunk_a_resultado(chunk) for chunk in chunks]}


def query_chunks(consulta: str, k: int, namespace: str = NAMESPACE_ESTRUCTURAL) -> list[PolicyChunk]:
    resultados = cliente_upstash.query(data=consulta, top_k=k, include_metadata=True, namespace=namespace)
    chunks = []
    for resultado in resultados:
        if resultado.metadata is None:
            raise RuntimeError(f"Vector {resultado.id} en Upstash no tiene metadata; ¿se indexó mal?")
        chunks.append(_chunk_desde_metadata(resultado.metadata))
    return chunks


def upsert_chunks(chunks: list[PolicyChunk], namespace: str = NAMESPACE_ESTRUCTURAL) -> None:
    vectores = [
        Vector(id=chunk.id, data=chunk.texto, metadata={**_metadata_de(chunk), "id": chunk.id})
        for chunk in chunks
    ]
    batch_size = 100
    for i in range(0, len(vectores), batch_size):
        cliente_upstash.upsert(vectors=vectores[i : i + batch_size], namespace=namespace)


def _chunk_a_resultado(chunk: PolicyChunk) -> dict:
    return {"seccion": chunk.seccion, "titulo": chunk.titulo, "texto": chunk.texto}


def _chunk_desde_metadata(metadata: dict) -> PolicyChunk:
    return PolicyChunk(
        id=metadata.get("id", ""),
        texto=metadata["texto"],
        seccion=metadata.get("seccion"),
        titulo=metadata.get("titulo"),
        estrategia=metadata["estrategia"],
        parametros=metadata.get("parametros"),
        num_tokens=metadata["num_tokens"],
    )


def _metadata_de(chunk: PolicyChunk) -> dict:
    return {
        "texto": chunk.texto,
        "seccion": chunk.seccion,
        "titulo": chunk.titulo,
        "estrategia": chunk.estrategia,
        "parametros": chunk.parametros,
        "num_tokens": chunk.num_tokens,
    }
