from dataclasses import dataclass
from typing import Literal

NAMESPACE_ESTRUCTURAL = "estructural"


@dataclass
class PolicyChunk:
    id: str
    texto: str
    seccion: str | None
    titulo: str | None
    estrategia: Literal["estructural", "tamano_fijo"]
    parametros: dict | None
    num_tokens: int
