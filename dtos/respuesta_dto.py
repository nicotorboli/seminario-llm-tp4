from pydantic import BaseModel


class AnalisisInterno(BaseModel):
    cadena_de_pensamiento: str
    politica_aplicada: str


class MetadatosClasificacion(BaseModel):
    categoria: str
    nivel_urgencia: str
    necesita_operador_humano: bool


class AccionYRespuesta(BaseModel):
    codigo_accion_sistema: str
    mensaje_al_cliente: str


class RespuestaLLM(BaseModel):
    analisis_interno: AnalisisInterno
    metadatos_clasificacion: MetadatosClasificacion
    accion_y_respuesta: AccionYRespuesta
