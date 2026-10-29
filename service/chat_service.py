from typing import Annotated, TypedDict

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import Runnable
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from integracion.upstash_integracion import buscar_politica
from dtos.respuesta_dto import RespuestaLLM
from prompts import SYSTEM_PROMPT
from settings import HOST, MODEL


class EstadoChat(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def procesar_mensaje(mensaje_usuario: str, temperature: float = 0.0) -> dict:
    grafo = _construir_grafo_de_tools(temperature)
    estado_final = grafo.invoke(
        {"messages": [SystemMessage(SYSTEM_PROMPT), HumanMessage(mensaje_usuario)]}
    )
    mensajes = estado_final["messages"]
    respuesta_final = _modelo_estructurado(temperature).invoke(mensajes)
    resultado = RespuestaLLM.model_validate_json(respuesta_final.content)  # type: ignore[arg-type]
    return resultado.model_dump()


def _construir_grafo_de_tools(temperature: float):
    def nodo_agente(state: EstadoChat) -> dict:
        respuesta = _modelo_con_tools(temperature).invoke(state["messages"])
        return {"messages": [respuesta]}

    def decidir_siguiente_paso(state: EstadoChat) -> str:
        ultimo_mensaje = state["messages"][-1]
        return "tools" if ultimo_mensaje.tool_calls else END  # type: ignore[attr-defined]

    grafo = StateGraph(EstadoChat)
    grafo.add_node("agente", nodo_agente)
    grafo.add_node("tools", ToolNode([buscar_politica]))
    grafo.set_entry_point("agente")
    grafo.add_conditional_edges("agente", decidir_siguiente_paso, {"tools": "tools", END: END})
    grafo.add_edge("tools", END)
    return grafo.compile()


def _modelo_con_tools(temperature: float) -> Runnable[LanguageModelInput, AIMessage]:
    return ChatOllama(model=MODEL, base_url=HOST, temperature=temperature).bind_tools([buscar_politica])


def _modelo_estructurado(temperature: float) -> ChatOllama:
    return ChatOllama(
        model=MODEL,
        base_url=HOST,
        temperature=temperature,
        format=RespuestaLLM.model_json_schema(),
    )
