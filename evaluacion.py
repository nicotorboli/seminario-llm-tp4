import json
import os

from dtos.politicas_dto import NAMESPACE_ESTRUCTURAL, PolicyChunk
from integracion.upstash_integracion import query_chunks
from service.politicas_service import (
    chunker_estructural,
    chunker_tamano_fijo,
    indexar_chunks,
)

_RUTA_POLITICAS = os.path.join(os.path.dirname(__file__), "politicas_ecommerce_integral.md")
_TAMANOS_TOKENS = (10, 100, 1000)
_OVERLAPS_PCT = (0.0, 0.10, 0.80)
_K_FIJO_PARA_GRILLA = 3
_VALORES_K = (2, 3, 4)
_MENSAJES_DE_PRUEBA = [
    "Compré una cafetera hace 45 días y dejó de funcionar, quiero que me la cambien ya.",
    "Ustedes tienen garantía de por vida en electrodomésticos, así que quiero el reembolso "
    "completo de mi licuadora que se rompió.",
    "Mi pedido llegó con 9 días de atraso y además en la factura me cobraron el envío dos veces.",
]


def correr_grilla() -> dict[str, dict]:
    with open(_RUTA_POLITICAS, encoding="utf-8") as archivo:
        markdown = archivo.read()
    resultados: dict[str, dict] = {}
    for tamano_tokens in _TAMANOS_TOKENS:
        for overlap_pct in _OVERLAPS_PCT:
            chunks = chunker_tamano_fijo(markdown, tamano_tokens, overlap_pct)
            namespace = _namespace_tamano_fijo(tamano_tokens, overlap_pct)
            resultados[namespace] = evaluar_combinacion(chunks, namespace)
    chunks_estructurales = chunker_estructural(markdown)
    resultados["grilla_estructural"] = evaluar_combinacion(chunks_estructurales, "grilla_estructural")
    return resultados


def correr_evaluacion_k() -> dict[int, dict]:
    return {k: evaluar_k(k) for k in _VALORES_K}


def evaluar_combinacion(chunks: list[PolicyChunk], namespace: str) -> dict:
    metricas = _metricas_de_chunks(chunks)
    indexar_chunks(chunks, namespace=namespace)
    metricas["resultados_por_mensaje"] = _recuperar_para_mensajes_de_prueba(namespace)
    return metricas


def evaluar_k(k: int) -> dict:
    resultados_por_mensaje: dict[str, list[dict]] = {}
    costo_tokens_total = 0
    for mensaje in _MENSAJES_DE_PRUEBA:
        chunks_recuperados = query_chunks(mensaje, k, namespace=NAMESPACE_ESTRUCTURAL)
        costo_tokens_total += sum(chunk.num_tokens for chunk in chunks_recuperados)
        resultados_por_mensaje[mensaje] = [
            {"seccion": chunk.seccion, "titulo": chunk.titulo, "texto": chunk.texto}
            for chunk in chunks_recuperados
        ]
    return {
        "k": k,
        "costo_tokens_total": costo_tokens_total,
        "resultados_por_mensaje": resultados_por_mensaje,
    }


def _recuperar_para_mensajes_de_prueba(namespace: str, k: int = _K_FIJO_PARA_GRILLA) -> dict[str, list[dict]]:
    resultados_por_mensaje: dict[str, list[dict]] = {}
    for mensaje in _MENSAJES_DE_PRUEBA:
        chunks_recuperados = query_chunks(mensaje, k, namespace=namespace)
        resultados_por_mensaje[mensaje] = [
            {"seccion": chunk.seccion, "titulo": chunk.titulo, "texto": chunk.texto}
            for chunk in chunks_recuperados
        ]
    return resultados_por_mensaje


def _metricas_de_chunks(chunks: list[PolicyChunk]) -> dict:
    return {
        "num_chunks": len(chunks),
        "costo_tokens_total": sum(chunk.num_tokens for chunk in chunks),
    }


def _namespace_tamano_fijo(tamano_tokens: int, overlap_pct: float) -> str:
    overlap_pct_label = round(overlap_pct * 100)
    return f"grilla_{tamano_tokens}_{overlap_pct_label}"


if __name__ == "__main__":
    resultado = {"grilla_chunking": correr_grilla(), "evaluacion_k": correr_evaluacion_k()}
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
