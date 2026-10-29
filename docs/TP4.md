# Trabajo Práctico 4: Generación aumentada por recuperación (RAG) para soporte automatizado

Formato de entrega: igual al TP anterior.

## Objetivo del Trabajo Práctico

Evolucionar el "motor de triaje y resolución inteligente" desarrollado en el trabajo anterior mediante la implementación de un sistema RAG (Retrieval-Augmented Generation). El sistema ya no dependerá de políticas fijas en el prompt; ahora deberá buscar dinámicamente las cláusulas correctas dentro de un corpus de documentos (Manual de Políticas de E-commerce) utilizando embeddings y una base de datos vectorial para fundamentar (grounding) su razonamiento y la respuesta final al cliente.

## Contexto del Problema

El departamento legal y de operaciones de la empresa de E-commerce ha actualizado el Manual de Políticas de Devoluciones, Envíos y Garantías. El documento es demasiado extenso para incluirlo completo dentro del contexto del prompt (además de ser ineficiente y costoso). Por otra parte, en el futuro se quiere poder modificar el dicho documento sin tener que cambiar el prompt.
El objetivo es construir un pipeline de RAG local o en la nube para que, cuando llegue un mensaje de un usuario, extraiga las políticas huérfanas o relevantes, las inyecte en el prompt construido para el TP anterior (sacando las políticas) y ejecute el proceso de pensamiento (Chain-of-Thought) basándose estrictamente en la documentación oficial actualizada.

## Requerimientos Técnicos

El flujo de ejecución del notebook debe extenderse para incluir obligatoriamente los siguientes componentes de RAG:
1. Ingesta y fragmentación (Chunking):
	- Cargar el documento de políticas provisto.
	- Dividir el texto en fragmentos (chunks) utilizando estrategias de tamaño fijo con solapamiento (overlap) o basadas en la estructura del documento.
2. Generación de Embeddings y Vector Store:
	- Indexar los fragmentos en una base de datos vectorial (ej. ChromaDB, FAISS, LanceDB o en memoria si es con embeddings locales).
	- Utilizar un modelo de embeddings adecuado (ej. text-embedding-3-small de OpenAI o un modelo de HuggingFace vía Ollama).
3. Recuperación Dinámica (Retrieval):
	- Ante el mensaje del usuario, realizar una búsqueda por similitud del coseno o distancia euclidiana para extraer los Top-K fragmentos más relevantes (donde \(K \in [2, 4]\)).
4. Prompt Inyectado y Salida Estructurada (Generación):
	- El prompt maestro del TP3 debe modificarse para aceptar una nueva variable de entrada: {contexto_politicas}.
	- El modelo debe mantener la salida JSON estructurada, pero ahora la propiedad politica_aplicada debe citar o resumir textualmente la política recuperada por el sistema RAG.

## Base de Conocimientos (Dataset de Políticas)

Usa el archivo politicas_ecommerce_integral.md. También pueden verificar la robustez de su propuesta con otro markdown con al menos 6 políticas detalladas. Ejemplo de contenido a incluir:
• Sección Envíos: Plazos de entrega según región, costos de reprogramación y procedimiento ante pérdidas de paquetes.
• Sección Garantías: Cobertura de electrodomésticos (90 días por falla de fábrica), exclusiones (daños por mal uso o agua).
• Sección Facturación: Plazos para solicitar notas de crédito (máximo 15 días hábiles después de la compra).

## Consignas del Entregable (Estructura del Notebook)

1. Configuración del Entorno y Librerías:
Instalación e importación de herramientas de procesamiento de texto y vectores (ej. langchain-text-splitters, chromadb, sentence-transformers, o las herramientas nativas del SDK elegido).
2. Pipeline de indexado (Embeddings e Indexación):
Código que lee el archivo de políticas, lo fragmenta y lo almacena en el Vector Store. Se debe documentar la estrategia de chunking elegida (tamaño del fragmento y solapamiento). Probar al menos con chunks de 10, 100 y 1000 tokens y con solapamiento de 0%, 10% y 80%. (9 combinaciones) y mostrar resultados de calidad y costo en tokens
3. Mecanismo de Recuperación (Retrieval):
Crear una función recuperar_contexto(mensaje_usuario: str, k: int) -> str que devuelva los fragmentos de texto consolidados. Evaluar como en el punto anterior el k en términos de calidad y costo.
4. Pipeline RAG Completo (procesar_mensaje_con_rag):
Modificar la función del TP 3 para que realice todo el flujo:

**Mensaje del Usuario** → **Retrieval** → **Prompt Maestro + Contexto** → **LLM** →**JSON Estructurado**

5. Evaluación de Casos de Negocio:
Probar el sistema con 3 casos borde que requieran políticas muy específicas.
	- Ejemplo: Un usuario que pide la devolución de una cafetera rota a los 45 días de compra (debe denegarse el reembolso directo pero ofrecer servicio técnico si la política lo avala).

## Criterios de Evaluación

+ Arquitectura de RAG Funcional: Correcta fragmentación del texto, generación de embeddings sin errores y almacenamiento/recuperación desde la base de datos vectorial.
+ Fidelidad de la Respuesta (Grounding): El LLM debe basar sus decisiones únicamente en el contexto recuperado. Si un usuario inventa una política falsa en su mensaje, el modelo debe ignorarla gracias al contexto del RAG.
+ Mantenimiento del Formato Estructurado : La inyección de texto variable (contexto) en el prompt no debe romper la habilidad del modelo para devolver el JSON con el esquema Pydantic estricto.
+ Documentación y Justificación Técnica: Explicación breve de por qué se eligieron ciertos tamaños de chunk y un análisis de qué sucedería si el recuperador trae información irrelevante (ruido).

