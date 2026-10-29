# Resultados: grilla de chunking y evaluación de "k"

## Upstash Vector

 Se ejecutó una evaluación empírica exhaustiva utilizando el script "evaluacion.py" conectado directamente a la base de datos vectorial en la nube **Upstash Vector** con el modelo de embeddings **text-embedding-3-smal**.

Se evaluo:
1. **La Grilla de 9 Combinaciones de Tamaño Fijo y Overlap** (10, 100 y 1000 tokens con 0%, 10% y 80% de solapamiento) comparada contra la estrategia **Estructural** por encabezado (`###`). Cada combinación fue indexada en un namespace independiente (`grilla_10_0`, `grilla_10_10`, `grilla_10_80`, `grilla_100_0`, etc.) y consultada con los mensajes de prueba del negocio.
2. **La Evaluación de $k \in \{2, 3, 4\}$** sobre el índice estructural de producción para medir la relación costo/calidad y el impacto del ruido.

---

## 1. Grilla de Tamaño Fijo + Overlap (9 combinaciones) vs. Estructural

Resultados medidos en Upstash Vector ejecutando [`evaluacion.correr_grilla()`] sobre `politicas_ecommerce_integral.md`:

| Estrategia | Tamaño (tokens) | Overlap | Chunks | Costo Tokens (Indexación) | Calidad de Recuperación | Comportamiento Semántico Observado |
|---|---|---|---|---|---|---|
| Tamaño fijo | 10 | 0% | 326 | 3.255 | **Muy Baja (Nula)** | Cláusulas mutiladas en fragmentos de 4 a 6 palabras. Top-1 trae `"ertura de postventa: * **Plazo"`. Imposible entender la política. |
| Tamaño fijo | 10 | 10% | 362 | 3.617 | **Muy Baja (Nula)** | Fragmentación crítica. Recupera pedazos aislados como `"Garantía:** Todos los electrodom"`. No aporta plazo ni excepciones. |
| Tamaño fijo | 10 | 80% | 1.624 | 16.238 | **Muy Baja (Nula)** | Multiplicación de costo x5 sin ganancia semántica. Frases truncadas como `"garantía limitada de 90 días corrid"`. |
| Tamaño fijo | 100 | 0% | 33 | 3.256 | **Media / Insuficiente** | Corte arbitrario de cláusulas. Recupera opciones de servicio técnico pero corta el encabezado que fija el plazo legal de 90 días. |
| Tamaño fijo | 100 | 10% | 37 | 3.616 | **Media / Insuficiente** | El solapamiento mínimo no resuelve la separación entre cobertura y exclusiones. Contexto incompleto para razonar. |
| Tamaño fijo | 100 | 80% | 159 | 15.896 | **Media / Ruido** | El solapamiento masivo genera dispersión y falsos positivos (recupera fragmentos de pérdida de paquetes en reclamos de cafeteras). |
| Tamaño fijo | 1000 | 0% | 4 | 3.256 | **Baja (Diluida)** | Chunks de medio documento. El embedding promedio pierde especificidad: ante reclamos de electrodomésticos el Top-1 trae políticas de logística. |
| Tamaño fijo | 1000 | 10% | 4 | 3.556 | **Baja (Diluida)** | Dilución semántica severa. Trae secciones completas irrelevantes, incrementando drásticamente el costo de inferencia del LLM. |
| Tamaño fijo | 1000 | 80% | 13 | 12.856 | **Baja (Muy Ruidosa)** | Máxima redundancia y saturación de contexto con texto irrelevante no relacionado con la consulta puntual del cliente. |
| **Estructural** | **Por cláusula (`###`)** | **0%** | **8** | **2.853** | **Óptima (100% Precisión)** | **Unidad jurídica autónoma.** Recupera exactamente la Sección 2.1 completa (plazo, cobertura y opciones de restitución) sin cortes. |

### Análisis de Costo y Factibilidad:
- **El overlap domina el costo de almacenamiento/embeddings**: Pasar de 0% a 80% de overlap incrementa el costo entre **4x y 5x** en todos los tamaños (ej. de 3.256 a 15.896 tokens en tamaño 100).
- **10 tokens es conceptual y técnicamente inviable**: Genera hasta 1.624 fragmentos para un texto de ~90 líneas. Cada chunk es apenas un fragmento de oración sin sentido jurídico.
- **1000 tokens degrada la precisión vectorial (*Embedding Dilution*)**: Al comprimir 1000 tokens en un único vector, los conceptos de electrodomésticos, envíos y facturación se mezclan en el espacio vectorial, provocando que el recuperador devuelva chunks logísticos ante quejas de garantías.
- **La estrategia estructural es la más eficiente**: Con solo **2.853 tokens** totales y 8 chunks, reduce a cero la redundancia y garantiza que el LLM reciba cláusulas completas con inicio, condiciones y fin.

---

## 2. Evaluación de `k` — Medición Real contra Upstash Vector

Se ejecutó [`evaluacion.correr_evaluacion_k()`] conectándose al índice en Upstash Vector (namespace `estructural`, 8 chunks con `text-embedding-3-small`). Se evaluaron los valores $k \in \{2, 3, 4\}$ sobre los 3 mensajes de prueba de negocio:

| $k$ | `costo_tokens_total` (3 mensajes) | Promedio tokens/mensaje | Secciones recuperadas por mensaje de prueba | Calidad de Grounding Observada |
|---|---|---|---|---|
| **2** | **2.283** | ~761 | • Cafetera (45 días): `2.1`, `SECCIÓN 4`<br>• Garantía de por vida: `2.1`, `2.2`<br>• Envío + Facturación: `1.1`, `1.3` | **Buena en casos directos**, pero omite cláusulas accesorias importantes (como exclusiones en casos límite). |
| **3** *(Default)* | **3.361** | ~1.120 | • Cafetera (45 días): `2.1`, `SECCIÓN 4`, `2.2`<br>• Garantía de por vida: `2.1`, `2.2`, `SECCIÓN 4`<br>• Envío + Facturación: `1.1`, `1.3`, `1.2` | **Óptima (Punto de Equilibrio)**: Aporta la cláusula principal, exclusiones y marco legal complementario sin saturar el prompt. |
| **4** | **4.471** | ~1.490 | • Cafetera (45 días): `2.1`, `SECCIÓN 4`, `2.2`, `1.3` *(ruido)*<br>• Garantía de por vida: `2.1`, `2.2`, `SECCIÓN 4`, `1.3` *(ruido)*<br>• Envío + Facturación: `1.1`, `1.3`, `1.2`, `3.1` | **Sobre-costo (+33%) y Ruido**: Comienza a arrastrar fragmentos desconectados (ej. pérdida de paquetes en reclamos de electrodomésticos). |

### Observaciones de la evaluación empírica de $k$:
- **$k=2$ (Bajo costo, riesgo de cobertura parcial)**: Logra el menor consumo de tokens (2.283), trayendo la cláusula principal (Sección 2.1). Sin embargo, en reclamos que requieren verificar exclusiones técnicas o plazos de revocación, la omisión de un tercer chunk puede forzar al modelo a escalar innecesariamente.
- **$k=3$ (Seleccionado)**: Recupera consistentemente la regla principal y sus cláusulas conexas (cobertura + exclusiones + plazos legales de revocación). Aporta el contexto necesario para que el razonamiento Chain-of-Thought contraste la situación real del cliente con el marco normativo.
- **$k=4$ (Aparición de Ruido)**: Incurre en un incremento innecesario de tokens (+1.110 tokens) e introduce cláusulas no pertinentes como la Sección 1.3 ("Pérdida de Paquetes") en consultas de reparación de pequeños electrodomésticos.

---

## 3. Calidad de Recuperación y Justificación Técnica de la Configuración Elegida

La configuración final adoptada para producción (**Chunking Estructural** + **$k=3$**) se sustenta en tres pilares:

1. **Preservación de la Unidad Semántica y Legal**:
   En documentos normativos o contractuales, un párrafo aislado no constituye una política: una regla solo tiene sentido junto con sus condiciones de validez, plazos y excepciones. El chunking estructural asegura que cada vector indexe la sección entera (`###`) con su título, cuerpo y viñetas.
2. **Eficiencia en Tokens y Costos**:
   El índice estructural consume únicamente **2.853 tokens** (frente a los más de 16.000 tokens de un chunking fijo con 80% de overlap). En inferencia, $k=3$ insume un promedio de ~1.120 tokens por consulta, balanceando exhaustividad y bajo consumo.
3. **Robustez del Grounding contra Alucinaciones**:
   En $k=3$, las búsquedas semánticas posicionan en los primeros lugares la Sección 2.1 (garantía de 90 días) y la Sección 4 (botón de arrepentimiento de 10 días), permitiendo al LLM fundamentar taxativamente por qué no corresponde un reembolso directo a los 45 días, pero sí la reparación técnica bajo garantía.

---

## 4. Análisis de Impacto del Ruido en el Recuperador (Información Irrelevante)

Uno de los requerimientos teóricos centrales del TP4 es analizar qué sucedería si el recuperador trae información irrelevante o con ruido al contexto del LLM.

### Consecuencias del ruido en el contexto:
1. **Dilución de la Atención (*Lost in the Middle*)**:
   Cuando fragmentos no pertinentes (ej. procedimientos de extravío logístico en una queja sobre un defecto eléctrico) saturan el prompt, los modelos de lenguaje tienden a perder foco sobre las cláusulas críticas, degradando la precisión de la respuesta.
2. **Riesgo de Falso Grounding y Alucinación Guiada**:
   Si el cliente realiza un planteo ambiguo y el recuperador devuelve una cláusula no aplicable pero con vocabulario similar, existe el riesgo de que el LLM intente "forzar" la aplicación de esa política para complacer al usuario, inventando una relación causa-efecto inexistente.
3. **Desperdicio de Tokens y Costo Operativo**:
   Inyectar chunks irrelevantes incrementa innecesariamente entre 400 y 800 tokens por inferencia. En un entorno de producción con miles de tickets diarios, esto multiplica la latencia y los costos de infraestructura de API.

### Mitigaciones implementadas en nuestra arquitectura:
- **Grounding Negativo en el System Prompt**: Se incluyeron directivas explícitas que instruyen al modelo a desestimar en su cadena de pensamiento (`analisis_interno.cadena_de_pensamiento`) cualquier política alegada o recuperada que no respalde estrictamente el caso.
- **Mecanismo de Salvaguarda (Escalamiento a Humano)**: Si los fragmentos recuperados no contienen una política aplicable con certeza, el modelo marca `necesita_operador_humano: true` y evita inventar soluciones.
- **RAG Agéntico por Tool Calling**: A diferencia de un RAG ingenuo que vectoriza el mensaje crudo del cliente (lleno de quejas, emoción o intentos de engaño), nuestro modelo reformula una consulta semántica precisa (`consulta="garantía electrodomésticos cafetera"`) mediante la herramienta `buscar_politica`, filtrando el ruido antes de consultar la base vectorial.
