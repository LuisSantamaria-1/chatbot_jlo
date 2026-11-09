# Interpretación y contexto del catálogo municipal — 3 de noviembre de 2026

La conversación adjunta mostraba una pérdida de contexto entre el clasificador y el gestor de diálogo. Una respuesta válida podía ser reconocida por el resolver y, aun así, descartarse porque el clasificador la asociaba a otra familia o a fuera de dominio. Las rectificaciones conservaban atributos incompatibles de la opción anterior. El segundo intento acababa mostrando listas con letras.

## Cambios compartidos por las familias de trámites

- El diálogo contrasta la respuesta con los atributos, alternativas y grupos del caso activo antes de cambiar de tema. Las solicitudes sobre un objeto nuevo siguen cambiando de contexto; una familia amplia no desplaza un procedimiento más específico.
- Una opción identificada aporta sus atributos al contexto. Las rectificaciones reemplazan los atributos incompatibles y pueden cambiar de grupo. «No quiero…» no selecciona la alternativa rechazada.
- La normalización conversacional admite verbos flexionados, jerga y una errata en palabras largas cuando solo existe una corrección posible. No transforma luz en luces, lotes en sublotes ni otro en otra. El preprocesamiento del modelo entrenado permanece intacto.
- Un índice TF-IDF de palabras y caracteres usa las descripciones de todas las macros para sugerir confirmaciones cuando la frase no coincide con una regla. Las variantes regulares como «fusionados» se comparan en ese índice; no convierten la similitud en una resolución directa.
- Los procedimientos sin macro se recuperan con sus nombres del catálogo y consultas de **train_nlp.csv**. No se utiliza test_nlp.csv para construir este índice. La recuperación puede corroborar una predicción insuficiente del clasificador y preguntar si se trata de ese procedimiento. La respuesta del ciudadano confirma la ficha antes de mostrar sus datos.
- Las aclaraciones se expresan con preguntas naturales, sin exigir letras ni números y sin botones de alternativas. Las selecciones antiguas siguen siendo compatibles. Las preguntas por medidas, modalidad o riesgo no se sustituyen por una suposición.
- Los comparadores numéricos conservan el significado de «más de». Una medida no anula condiciones explícitas como demolición parcial, sótano o explosivos.

La respuesta final conserva el nombre y los requisitos. Costo y plazo se responden cuando se solicitan. El contrato de `/api/chat` conserva sus campos; `opciones` queda vacío al aclarar y mantiene Requisitos, Costo, Plazo y Otro trámite al resolver.

## Validación reproducible

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q --reporte-csv reports/dialogo_catalogo.csv
.\.venv\Scripts\python.exe scripts/informar_cobertura_dialogo.py
.\.venv\Scripts\python.exe scripts/verificar_respuestas_claras.py --mysql
```

La cobertura añadida recorre 925 formulaciones de 185 alternativas en 39 familias por la API con el clasificador real, además de 185 rectificaciones entre alternativas y 16 consultas de procedimientos individuales sin título oficial. Los 925 casos parten con la familia activa: comprueban la comprensión contextual, no la clasificación inicial de toda consulta posible. Se conservan las comprobaciones de campos y datos para los 239 procedimientos y las variantes con Revisor Urbano.

Resultado de la revisión anterior: **3556 pruebas aprobadas**. La tabla exportada contiene las 925 formulaciones de macros y las 16 consultas individuales, todas resueltas. Aquella comprobación HTTP con MySQL aprobó sus **38 turnos** y cerró el servidor temporal.

`reports/cobertura_dialogo.md` contiene la tabla frase/camino/trámite. `reports/respuestas_claras_mysql.md` conserva los 38 turnos comprobados por HTTP con MySQL, incluida la transcripción recibida. El servidor de comprobación usa un puerto temporal y se cierra al terminar; no inicia otra instancia en el puerto 5000.

La suite usa SQLite temporal y no comparte la rotación del archivo de logs del servidor real. La comprobación con `--mysql` sí registra sus consultas sintéticas en la auditoría habitual.

## Modelo y límites de la comprobación

No se modificaron los CSV de entrenamiento/prueba ni el archivo joblib. `evaluar_tfidf_v2.py` reproduce, con las particiones actuales de 2741/686 consultas, exactitud **91,40 %**, F1 macro **91,08 %**, F1 ponderado **91,35 %**, exactitud CV **92,56 %** y F1 macro CV **92,66 %**. Se corrigieron únicamente los rótulos que imprimían cantidades antiguas de ejemplos en ese script.

Las pruebas son regresiones sobre casos definidos, no una garantía de comprender cualquier frase futura. Cuando la descripción sigue siendo ambigua, Leonardito pregunta el dato que falta o propone una confirmación, sin inventar requisitos ni importes. Los hechos y valores finales se leen del catálogo municipal.

## Revisión de las 80 consultas y la conversación completa

La revisión posterior incorpora `tests/test_revision_ciudadana.py` y las consultas originales en `tests/casos_revision_ciudadana.json`. Se verifican las 80 consultas independientes, cambios desde otros asuntos, la transcripción de 132 turnos, correcciones de grupo, preguntas por varios campos y dos asuntos distintos en el mismo mensaje.

- Costo y plazo se conservan mientras se aclara un caso, sin arrastrar los campos de una nueva solicitud. Se reconocen preguntas como «en qué tiempo», «es gratis» y «cuánto sale».
- Una compra del local se distingue de una transferencia de licencia; un carnet personal se distingue del certificado sanitario del establecimiento. Esas consultas requieren aclaración.
- Las definiciones de ITSE, parámetros y declaratoria explican el concepto sin seleccionar un procedimiento por defecto. La categoría de riesgo no se deduce del tamaño o tipo de negocio.
- Una corrección de grupo residencial descarta la elección anterior. Las expresiones con letras repetidas y variantes frecuentes se normalizan en el diálogo. El clasificador conserva el preprocesamiento de entrenamiento.
- Dos consultas guardan por separado sus asuntos y campos. El ciudadano puede elegir con sus palabras y continuar luego con la consulta pendiente.
- Un plazo común solo se muestra cuando también coincide en las alternativas con Revisor Urbano. Se conservan los días calendario y los plazos inmediatos.

Resultado final: **3738 pruebas aprobadas**, sin fallos. La evidencia está en `reports/revision_ciudadana_80/pytest.xml`; la ejecución íntegra, en `scratch/pruebas_revision_ciudadana_verificadas.txt`.

El puerto 5000 atendía una versión antigua en memoria. Se reinició exclusivamente la instancia de este proyecto y se comprobaron **235 solicitudes HTTP**: las 80 consultas, los 132 turnos y 23 consultas adicionales de regresión. `reports/revision_ciudadana_80/http_real.json` registra las respuestas, sin diferencias con el CSV en las fichas consultadas. La cabecera `X-Leonardito-Revision` identifica el código cargado al arrancar; la revisión verificada es `947788a4e79a`. Solo hay una instancia atendiendo el puerto.

La auditoría inicial de las 239 fichas encontró cambios de prueba solo en T_016: costo S/ 140.00, plazo de 10 días y un requisito «Requisito nuevo». Se guardó el catálogo previo en `backups/respaldo_catalogo_20261103_151837_632835.json` y se restauró esa ficha desde el CSV validado: S/ 240.00, 20 días hábiles y sus siete requisitos. La comparación posterior de MySQL confirmó cero diferencias. No se añadió sincronización automática al arranque: las ediciones administrativas siguen persistiendo.

La evaluación original se repitió en una carpeta aislada de informes. Sus métricas coinciden con las indicadas arriba; `reports/revision_ciudadana_80/evaluacion/integridad.json` verifica que los tres CSV de NLP y el modelo joblib conservan su contenido. El contrato de `/api/chat` y los cuatro botones de seguimiento se mantienen. El efecto visual de pensamiento conserva su duración mínima de tres segundos.
