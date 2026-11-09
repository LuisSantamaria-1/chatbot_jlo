# Anexos de pruebas del chatbot municipal Leonardito

Ejecución: 03/11/2026. 3556 pruebas automatizadas aprobadas. 20 fichas de caja negra y 12 de caja blanca.

Los códigos R-ANX son identificadores de este anexo. La ejecución corresponde a SQLite temporal, API HTTP y funciones internas; no a una verificación manual de interfaz ni a disponibilidad productiva.

## CN-01 Acceso al portal ciudadano

DESCRIPCIÓN DE PRUEBAS DE CAJA NEGRA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-01 - Acceso web al portal municipal |
| Módulo/Área Funcional/Subproceso | Portal web municipal |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-01 |
| Descripción del requisito | El sistema debe entregar la página ciudadana y permitir localizar el acceso administrativo. |
| Código de prueba | CN-01 |
| Caso de prueba | Acceso al portal ciudadano |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | Disponibilidad funcional del portal y enlace de administración. |
| Datos de entrada/Acciones de entrada | GET / y consulta del enlace de acceso administrativo. |
| Resultado esperado | HTTP 200 en la página principal; enlace de administración dirigido a /admin. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Solicitar la página principal del sistema. 2. Comprobar el código HTTP y la presencia del enlace administrativo. |
| Ramas y condiciones evaluadas | No aplica a la técnica de caja negra. |
| Resultado obtenido | Exitoso. La página principal respondió HTTP 200 y se verificó el enlace /admin. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 2. |
| Observaciones | La prueba verifica la entrega HTTP del portal. No constituye una evaluación visual entre navegadores. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_admin.py::test_paginas_html_responden_200_con_csp; tests/test_politica_general.py::test_licencia_ambigua_y_acceso_admin |

## CN-02 Saludo y presentación del asistente

DESCRIPCIÓN DE PRUEBAS DE CAJA NEGRA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-02 - Saludo y presentación del asistente |
| Módulo/Área Funcional/Subproceso | Chat ciudadano |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-02 |
| Descripción del requisito | El asistente debe responder a saludos y consultas de presentación con mensajes comprensibles. |
| Código de prueba | CN-02 |
| Caso de prueba | Saludo y presentación del asistente |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | Interacción inicial y presentación de Leonardito. |
| Datos de entrada/Acciones de entrada | POST /api/chat con «hola» y «como te llamas». |
| Resultado esperado | HTTP 200; respuesta de saludo o charla casual con un mensaje de presentación. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Iniciar una sesión ciudadana nueva. 2. Enviar cada mensaje y revisar el estado y el texto recibido. |
| Ramas y condiciones evaluadas | No aplica a la técnica de caja negra. |
| Resultado obtenido | Exitoso. Las consultas devolvieron HTTP 200 y las categorías saludo y charla_casual correspondientes. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 2. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_chat.py::test_api_chat_saludo; tests/test_chat.py::test_api_chat_charla_casual |

## CN-03 Consulta de requisitos de un trámite

DESCRIPCIÓN DE PRUEBAS DE CAJA NEGRA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-03 - Comprensión de consultas y exactitud del catálogo |
| Módulo/Área Funcional/Subproceso | Orientación sobre el TUPA |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-03 |
| Descripción del requisito | El chatbot debe identificar el trámite consultado y presentar sus requisitos. |
| Código de prueba | CN-03 |
| Caso de prueba | Consulta de requisitos de un trámite |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | Identificación de numeración municipal y consulta de requisitos. |
| Datos de entrada/Acciones de entrada | «requisitos para certificado de numeracion municipal». |
| Resultado esperado | HTTP 200; status=success y trámite T_015. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Abrir una sesión nueva. 2. Enviar la consulta completa. 3. Revisar el identificador y la respuesta. |
| Ramas y condiciones evaluadas | No aplica a la técnica de caja negra. |
| Resultado obtenido | Exitoso. Se identificó T_015 y se obtuvo una respuesta success con HTTP 200. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 1. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_chat.py::test_api_chat_requisitos_tramite |

## CN-04 Lenguaje cotidiano y errores de escritura

DESCRIPCIÓN DE PRUEBAS DE CAJA NEGRA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-03 - Comprensión de consultas y exactitud del catálogo |
| Módulo/Área Funcional/Subproceso | Comprensión de consultas ciudadanas |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-03 |
| Descripción del requisito | El chatbot debe admitir expresiones cotidianas y errores frecuentes sin exigir el título del trámite. |
| Código de prueba | CN-04 |
| Caso de prueba | Lenguaje cotidiano y errores de escritura |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | Comprensión de «casita», «tamos remodelando» y errores en «edificio». |
| Datos de entrada/Acciones de entrada | «en mi casita pe»; «tamos remodelando el edifcio multifamiliar» y variantes de «edifcio». |
| Resultado esperado | Matrimonio a domicilio: T_020. Remodelación de edificio multifamiliar: T_145. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Consultar un matrimonio y responder con el lugar en lenguaje cotidiano. 2. Consultar una ampliación y describir la remodelación con las variantes de escritura. 3. Comparar los trámites devueltos. |
| Ramas y condiciones evaluadas | No aplica a la técnica de caja negra. |
| Resultado obtenido | Exitoso. Las variantes ejecutadas conservaron T_020 para domicilio y T_145 para remodelación multifamiliar. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 4. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_contexto_catalogo.py::test_transcripcion_del_ciudadano; tests/test_contexto_catalogo.py::test_erratas_largas_sin_exigir_frase_exacta |

## CN-05 Aclaración de una consulta ambigua

DESCRIPCIÓN DE PRUEBAS DE CAJA NEGRA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-04 - Desambiguación y resolución controlada |
| Módulo/Área Funcional/Subproceso | Diálogo sobre matrimonio civil |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-04 |
| Descripción del requisito | Cuando falte información para distinguir una alternativa, el chatbot debe formular una pregunta de aclaración. |
| Código de prueba | CN-05 |
| Caso de prueba | Aclaración de una consulta ambigua |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | Consulta ambigua y presentación sin opciones obligatorias por número. |
| Datos de entrada/Acciones de entrada | «quiero casarme» y «que?». |
| Resultado esperado | Respuesta clarification; pregunta sobre el caso sin exigir números ni mostrar un trámite arbitrario. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Enviar la solicitud general de matrimonio. 2. Revisar la pregunta de aclaración. 3. Pedir una explicación y verificar que continúe la aclaración. |
| Ramas y condiciones evaluadas | No aplica a la técnica de caja negra. |
| Resultado obtenido | Exitoso. Se obtuvo clarification; la respuesta no exigió «Respóndeme con» ni mostró una lista numerada. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 1. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_dialogo_natural.py::test_aclaraciones_sin_numeros |

## CN-06 Costo y plazo con contexto conversacional

DESCRIPCIÓN DE PRUEBAS DE CAJA NEGRA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-05 - Consulta separada de requisitos costo y plazo |
| Módulo/Área Funcional/Subproceso | Seguimiento de consultas |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-05 |
| Descripción del requisito | El asistente debe conservar el trámite activo para responder consultas posteriores de costo y plazo. |
| Código de prueba | CN-06 |
| Caso de prueba | Costo y plazo con contexto conversacional |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | Seguimiento de numeración municipal sin repetir su nombre. |
| Datos de entrada/Acciones de entrada | Consultar numeración; después «cuanto cuesta», «gracias» y «y cuanto demora». |
| Resultado esperado | T_015 se conserva; costo S/ 90.30; plazo 0 días hábiles, válido como atención inmediata. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Consultar requisitos de numeración municipal. 2. Preguntar el costo. 3. Agradecer y preguntar el plazo sin repetir el trámite. |
| Ramas y condiciones evaluadas | No aplica a la técnica de caja negra. |
| Resultado obtenido | Exitoso. Se mantuvo T_015; el costo fue S/ 90.30 y el plazo registrado fue 0 días hábiles. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 2. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_conversacion_ciudadana.py::test_conversacion_completa_y_cambio_de_tramite; tests/test_chat.py::test_plazo_t015_se_muestra_como_dato_valido |

## CN-07 Consulta de costo sin trámite previo

DESCRIPCIÓN DE PRUEBAS DE CAJA NEGRA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-05 - Consulta separada de requisitos costo y plazo |
| Módulo/Área Funcional/Subproceso | Seguimiento sin contexto |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-05 |
| Descripción del requisito | El chatbot debe solicitar el trámite cuando el ciudadano pregunta un costo sin contexto previo. |
| Código de prueba | CN-07 |
| Caso de prueba | Consulta de costo sin trámite previo |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | Recuperación de una consulta incompleta. |
| Datos de entrada/Acciones de entrada | Sesión nueva: «cuanto cuesta»; después «certificado de numeracion municipal». |
| Resultado esperado | Primero solicita identificar el trámite; luego responde el costo S/ 90.30 de T_015. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Abrir una sesión sin consultas anteriores. 2. Preguntar el costo sin indicar el trámite. 3. Indicar numeración municipal y comprobar el dato devuelto. |
| Ramas y condiciones evaluadas | No aplica a la técnica de caja negra. |
| Resultado obtenido | Exitoso. La primera respuesta fue fallback sin trámite definido; al precisarlo se respondió T_015 con S/ 90.30. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 1. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_conversacion_ciudadana.py::test_sin_contexto_conserva_pregunta |

## CN-08 Rectificación de una alternativa elegida

DESCRIPCIÓN DE PRUEBAS DE CAJA NEGRA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-06 - Continuidad y rectificación de la conversación |
| Módulo/Área Funcional/Subproceso | Diálogo sobre habilitación urbana |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-06 |
| Descripción del requisito | El ciudadano debe poder corregir su caso sin reiniciar la conversación ni escribir una letra de menú. |
| Código de prueba | CN-08 |
| Caso de prueba | Rectificación de una alternativa elegida |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | Cambio entre inversión pública, vivienda estatal y concesión. |
| Datos de entrada/Acciones de entrada | «inversion publica»; «nooo, era vivienda estatal me confundi»; «era por concesion». |
| Resultado esperado | La secuencia resuelve T_075, T_076 y nuevamente T_075 dentro del contexto de habilitación urbana. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Iniciar la consulta de habilitación urbana y precisar proyecto del Estado. 2. Indicar inversión pública. 3. Corregir a vivienda estatal y luego a concesión. |
| Ramas y condiciones evaluadas | No aplica a la técnica de caja negra. |
| Resultado obtenido | Exitoso. La conversación devolvió T_075 → T_076 → T_075, conservando el tema municipal. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 1. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_contexto_catalogo.py::test_transcripcion_del_ciudadano |

## CN-09 Cambio de tema durante la conversación

DESCRIPCIÓN DE PRUEBAS DE CAJA NEGRA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-06 - Continuidad y rectificación de la conversación |
| Módulo/Área Funcional/Subproceso | Diálogo entre trámites distintos |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-06 |
| Descripción del requisito | El chatbot debe permitir consultar otro trámite y actualizar el asunto de la conversación. |
| Código de prueba | CN-09 |
| Caso de prueba | Cambio de tema durante la conversación |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | Transición de puesto de mercado a autorización de feria. |
| Datos de entrada/Acciones de entrada | «quiero tomar el puesto del mercado porque se murio mi tio el dueño»; después «como saco permiso para un puesto de feria?». |
| Resultado esperado | Primera consulta: T_051. Nueva consulta: T_062, sin repetir el trámite anterior. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Describir la sucesión del puesto de mercado. 2. Consultar su costo. 3. Solicitar después el permiso relacionado con una feria. |
| Ramas y condiciones evaluadas | No aplica a la técnica de caja negra. |
| Resultado obtenido | Exitoso. Se resolvió la sucesión como T_051 y la consulta de feria como T_062. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 1. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_contexto_catalogo.py::test_transcripcion_del_ciudadano |

## CN-10 Explicación de un término del trámite

DESCRIPCIÓN DE PRUEBAS DE CAJA NEGRA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-07 - Explicación de términos municipales |
| Módulo/Área Funcional/Subproceso | Orientación sobre separación y divorcio |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-07 |
| Descripción del requisito | El asistente debe explicar términos del procedimiento sin interpretar la pregunta como una elección. |
| Código de prueba | CN-10 |
| Caso de prueba | Explicación de un término del trámite |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | Explicación de separación y divorcio ulterior. |
| Datos de entrada/Acciones de entrada | «quiero divorciarme»; «que es eso»; «no se que es divorcio ulterior»; «no». |
| Resultado esperado | Las preguntas reciben una explicación sin id_tramite; la respuesta posterior «no» resuelve T_009. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Iniciar la consulta de divorcio. 2. Pedir las explicaciones indicadas. 3. Responder que no se tiene la separación aprobada. |
| Ramas y condiciones evaluadas | No aplica a la técnica de caja negra. |
| Resultado obtenido | Exitoso. Se recibieron respuestas explicar_concepto sin seleccionar un trámite; después se resolvió T_009. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 1. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_respuestas_claras.py::test_explicar_conceptos_no_selecciona_el_tramite |

## CN-11 Atención de consultas fuera del ámbito municipal

DESCRIPCIÓN DE PRUEBAS DE CAJA NEGRA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-08 - Restricción al ámbito municipal |
| Módulo/Área Funcional/Subproceso | Límite temático del chatbot |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-08 |
| Descripción del requisito | El chatbot debe mantener su alcance en trámites y servicios del catálogo municipal. |
| Código de prueba | CN-11 |
| Caso de prueba | Atención de consultas fuera del ámbito municipal |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | Rechazo de consultas ajenas, con y sin trámite activo. |
| Datos de entrada/Acciones de entrada | «cuanto cuesta una pizza», «precio de bitcoin», «cuando juega peru» y consultas de receta o poema. |
| Resultado esperado | Respuesta fallback sin datosTramite ni una ficha municipal tomada por error. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Probar cada consulta en una sesión nueva. 2. Repetir las consultas después de activar un trámite municipal. 3. Verificar la ausencia de datos de un trámite en las respuestas. |
| Ramas y condiciones evaluadas | No aplica a la técnica de caja negra. |
| Resultado obtenido | Exitoso. Las diez combinaciones de consulta y contexto devolvieron fallback sin datosTramite. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 10. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_conversacion_ciudadana.py::test_limite_municipal |

## CN-12 Respuesta ante frustración del ciudadano

DESCRIPCIÓN DE PRUEBAS DE CAJA NEGRA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-09 - Atención de frustración |
| Módulo/Área Funcional/Subproceso | Atención conversacional |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-09 |
| Descripción del requisito | Las expresiones de molestia deben recibir una respuesta empática y permitir continuar la consulta municipal. |
| Código de prueba | CN-12 |
| Caso de prueba | Respuesta ante frustración del ciudadano |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | Detección de frustración y continuidad de un trámite anterior. |
| Datos de entrada/Acciones de entrada | Activar T_015; iniciar una consulta de licencia; «no me ayudas en nada, pesimo servicio»; «y cuanto cuesta». |
| Resultado esperado | Respuesta frustration; el seguimiento del costo conserva T_015. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Consultar numeración municipal. 2. Plantear una consulta de licencia y expresar frustración. 3. Preguntar el costo del trámite anterior. |
| Ramas y condiciones evaluadas | No aplica a la técnica de caja negra. |
| Resultado obtenido | Exitoso. Se obtuvo frustration y el seguimiento volvió a responder sobre T_015. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 1. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_conversacion_ciudadana.py::test_frustracion_interrumpe_menu_y_conserva_tramite |

## CN-13 Validación de solicitudes vacías o incompletas

DESCRIPCIÓN DE PRUEBAS DE CAJA NEGRA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-10 - Validación de mensajes recibidos |
| Módulo/Área Funcional/Subproceso | API del chat |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-10 |
| Descripción del requisito | El sistema debe rechazar solicitudes sin un mensaje válido mediante respuestas controladas. |
| Código de prueba | CN-13 |
| Caso de prueba | Validación de solicitudes vacías o incompletas |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | Tratamiento de mensaje vacío y cuerpo JSON sin mensaje. |
| Datos de entrada/Acciones de entrada | POST /api/chat con {"mensaje":""} y con {}. |
| Resultado esperado | HTTP 400; el mensaje vacío produce fallback y el cuerpo vacío produce error. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Enviar una cadena vacía como mensaje. 2. Enviar un objeto JSON vacío. 3. Comprobar los códigos HTTP y los estados de respuesta. |
| Ramas y condiciones evaluadas | No aplica a la técnica de caja negra. |
| Resultado obtenido | Exitoso. Ambas solicitudes devolvieron HTTP 400; sus estados fueron fallback y error respectivamente. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 2. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_chat.py::test_api_chat_mensaje_vacio; tests/test_chat.py::test_api_chat_payload_invalido |

## CN-14 Despedida y cierre del contexto activo

DESCRIPCIÓN DE PRUEBAS DE CAJA NEGRA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-11 - Gestión del contexto de sesión |
| Módulo/Área Funcional/Subproceso | Cierre de conversación |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-11 |
| Descripción del requisito | La despedida debe cerrar la consulta y evitar reutilizar el trámite en una pregunta posterior sin contexto. |
| Código de prueba | CN-14 |
| Caso de prueba | Despedida y cierre del contexto activo |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | Finalización de la conversación y nueva consulta de costo. |
| Datos de entrada/Acciones de entrada | Completar una consulta; «adios»; después «cuanto cuesta». |
| Resultado esperado | La despedida devuelve despedida; la nueva pregunta de costo no responde con el trámite cerrado. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Realizar una conversación municipal. 2. Enviar la despedida. 3. Preguntar un costo sin volver a indicar el trámite. |
| Ramas y condiciones evaluadas | No aplica a la técnica de caja negra. |
| Resultado obtenido | Exitoso. Se obtuvo despedida y la consulta posterior de costo devolvió fallback. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 1. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_conversacion_ciudadana.py::test_conversacion_completa_y_cambio_de_tramite |

## CN-15 Exactitud de los datos en los 239 trámites

DESCRIPCIÓN DE PRUEBAS DE CAJA NEGRA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-03 - Comprensión de consultas y exactitud del catálogo |
| Módulo/Área Funcional/Subproceso | Catálogo municipal y respuestas del chat |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-03 |
| Descripción del requisito | Requisitos, costo y plazo deben corresponder al trámite consultado y mostrarse según la información solicitada. |
| Código de prueba | CN-15 |
| Caso de prueba | Exactitud de los datos en los 239 trámites |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | Separación de campos y concordancia con el catálogo fuente. |
| Datos de entrada/Acciones de entrada | Cada uno de los 239 códigos del TUPA; luego «cuanto cuesta» y «cuanto demora». |
| Resultado esperado | Nombre y requisitos correctos al inicio; costo y plazo correctos en sus consultas, sin añadir los otros campos. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | El CSV local validado es el oráculo de datos. Esta prueba verifica exactitud de fichas, no comprensión de toda frase posible. |
| Pasos de la prueba | 1. Recorrer los 239 registros del catálogo fuente. 2. Solicitar cada ficha y contrastar nombre y requisitos. 3. Preguntar costo y plazo por separado y compararlos con el mismo registro. |
| Ramas y condiciones evaluadas | No aplica a la técnica de caja negra. |
| Resultado obtenido | Exitoso. Los 239 casos parametrizados aprobaron la concordancia de datos y la separación de requisitos, costo y plazo. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 239. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_respuestas_claras.py::test_campos_separados_para_cada_tramite |

## CN-16 Autenticación administrativa válida e inválida

DESCRIPCIÓN DE PRUEBAS DE CAJA NEGRA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-12 - Autenticación y control administrativo |
| Módulo/Área Funcional/Subproceso | Administración y autenticación |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-12 |
| Descripción del requisito | Solo las credenciales administrativas válidas deben permitir iniciar una sesión. |
| Código de prueba | CN-16 |
| Caso de prueba | Autenticación administrativa válida e inválida |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | Inicio de sesión con contraseña correcta e incorrecta. |
| Datos de entrada/Acciones de entrada | POST /api/admin/login con usuario admin y contraseña efímera del entorno de pruebas; repetir con contraseña incorrecta. |
| Resultado esperado | Credenciales válidas: HTTP 200 y success. Contraseña incorrecta: HTTP 401 y error. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Usar únicamente la cuenta efímera de pruebas. Las contraseñas y sus hashes no se incluyen en el anexo. |
| Pasos de la prueba | 1. Enviar las credenciales de la cuenta administrativa temporal. 2. Comprobar el inicio de sesión. 3. Repetir el envío con una contraseña incorrecta. |
| Ramas y condiciones evaluadas | No aplica a la técnica de caja negra. |
| Resultado obtenido | Exitoso. El acceso válido devolvió HTTP 200 y el intento con contraseña incorrecta devolvió HTTP 401. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 2. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_admin.py::test_admin_login_correcto; tests/test_admin.py::test_admin_login_password_incorrecto |

## CN-17 Bloqueo de acceso administrativo sin sesión

DESCRIPCIÓN DE PRUEBAS DE CAJA NEGRA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-12 - Autenticación y control administrativo |
| Módulo/Área Funcional/Subproceso | Protección del panel y de la API |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-12 |
| Descripción del requisito | El panel y las operaciones administrativas deben exigir una sesión administrativa válida. |
| Código de prueba | CN-17 |
| Caso de prueba | Bloqueo de acceso administrativo sin sesión |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | Acceso directo al panel y a operaciones CRUD sin autenticación. |
| Datos de entrada/Acciones de entrada | GET /admin; GET, POST, PUT y DELETE a rutas /api/admin/tramites sin sesión. |
| Resultado esperado | El panel redirige a /admin/login; las operaciones de la API responden HTTP 401. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Abrir un cliente sin sesión. 2. Solicitar directamente el panel. 3. Intentar listar, crear, editar y eliminar un trámite por API. |
| Ramas y condiciones evaluadas | No aplica a la técnica de caja negra. |
| Resultado obtenido | Exitoso. El panel no se entregó sin sesión y las operaciones administrativas probadas devolvieron HTTP 401. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 8. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_admin.py::test_html_admin_exige_sesion_antes_de_enviar_panel; tests/test_admin.py::test_admin_get_tramites_sin_sesion; tests/test_admin.py::test_admin_post_tramite_sin_sesion; tests/test_admin.py::test_admin_put_tramite_sin_sesion; tests/test_admin.py::test_admin_delete_tramite_sin_sesion |

## CN-18 Creación edición y eliminación de un trámite

DESCRIPCIÓN DE PRUEBAS DE CAJA NEGRA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-13 - Gestión y validación del catálogo |
| Módulo/Área Funcional/Subproceso | Administración del catálogo TUPA |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-13 |
| Descripción del requisito | El administrador autenticado debe poder gestionar los registros del catálogo. |
| Código de prueba | CN-18 |
| Caso de prueba | Creación edición y eliminación de un trámite |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | Operaciones CRUD sobre un trámite temporal. |
| Datos de entrada/Acciones de entrada | T_990, nombre de prueba, costo 15.00 soles, plazo 2 días hábiles y dos requisitos; actualizar nombre y costo a 25.00 soles. |
| Resultado esperado | Creación HTTP 201; actualización HTTP 200; eliminación HTTP 200. El catálogo vuelve a 239 registros. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | El alta y la eliminación se ejecutan en SQLite temporal; no se modifica el catálogo MySQL de uso real. |
| Pasos de la prueba | 1. Iniciar sesión administrativa. 2. Crear T_990 con sus datos de prueba. 3. Actualizar su nombre y costo. 4. Eliminar T_990 y comprobar el conteo final. |
| Ramas y condiciones evaluadas | No aplica a la técnica de caja negra. |
| Resultado obtenido | Exitoso. Se obtuvo la secuencia HTTP 201/200/200; el catálogo terminó con 239 trámites. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 1. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_admin.py::test_admin_escritura_con_sesion_crud_y_limpieza |

## CN-19 Rechazo de datos administrativos inválidos

DESCRIPCIÓN DE PRUEBAS DE CAJA NEGRA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-13 - Gestión y validación del catálogo |
| Módulo/Área Funcional/Subproceso | Validación del catálogo |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-13 |
| Descripción del requisito | El sistema debe impedir el registro de códigos inválidos o duplicados y de trámites sin requisitos. |
| Código de prueba | CN-19 |
| Caso de prueba | Rechazo de datos administrativos inválidos |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | Validaciones de alta administrativa. |
| Datos de entrada/Acciones de entrada | Alta con código de formato inválido; código TUPA existente; nombre mayor de 1024 caracteres; lista de requisitos vacía. |
| Resultado esperado | HTTP 400 en formato, longitud o requisitos inválidos; HTTP 409 en código duplicado. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Iniciar sesión administrativa. 2. Enviar cada variante inválida por separado. 3. Comparar los códigos de rechazo y comprobar que no se registra un trámite válido a partir del envío. |
| Ramas y condiciones evaluadas | No aplica a la técnica de caja negra. |
| Resultado obtenido | Exitoso. Las validaciones devolvieron HTTP 400 y el intento duplicado devolvió HTTP 409. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 4. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_admin.py::test_admin_post_id_formato_invalido; tests/test_admin.py::test_admin_post_codigo_duplicado; tests/test_admin.py::test_admin_post_nombre_demasiado_largo; tests/test_admin.py::test_admin_post_tramite_sin_requisitos |

## CN-20 Consulta administrativa del historial de conversaciones

DESCRIPCIÓN DE PRUEBAS DE CAJA NEGRA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-14 - Auditoría y consulta de conversaciones |
| Módulo/Área Funcional/Subproceso | Monitoreo de conversaciones |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-14 |
| Descripción del requisito | El historial de conversaciones debe estar disponible para el administrador y protegido frente a consultas sin sesión. |
| Código de prueba | CN-20 |
| Caso de prueba | Consulta administrativa del historial de conversaciones |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | Acceso autenticado al historial y respuesta paginada. |
| Datos de entrada/Acciones de entrada | GET /api/admin/conversaciones sin sesión; repetir autenticado con ?page=1&limit=10. |
| Resultado esperado | Sin sesión: HTTP 401. Con sesión: HTTP 200, lista de conversaciones y metadatos del total. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Solicitar el historial sin autenticación. 2. Iniciar sesión administrativa. 3. Solicitar la primera página y revisar la lista y los metadatos. |
| Ramas y condiciones evaluadas | No aplica a la técnica de caja negra. |
| Resultado obtenido | Exitoso. Se verificó HTTP 401 sin sesión y HTTP 200 con lista y total cuando la sesión fue válida. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 2. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_log.py::test_admin_conversaciones_requiere_autenticacion; tests/test_log.py::test_admin_conversaciones_con_sesion_paginado |

## CB-01 Normalización de texto y jerga peruana

DESCRIPCIÓN DE PRUEBAS DE CAJA BLANCA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-03 - Comprensión de consultas y exactitud del catálogo |
| Módulo/Área Funcional/Subproceso | NLP / preprocesamiento de texto |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-03 |
| Descripción del requisito | La función preprocesar_texto debe producir una representación uniforme para las variantes léxicas previstas. |
| Código de prueba | CB-01 |
| Caso de prueba | Normalización de texto y jerga peruana |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | backend/nlp/preprocesamiento.py: preprocesar_texto; traducción de jerga. |
| Datos de entrada/Acciones de entrada | Diez entradas, entre ellas «trámite de numeración», «kiero lisencia altoke pa mi tienda» y «ayuda xfa». |
| Resultado esperado | «tramite de numeracion»; «quiero licencia rapido para mi tienda»; «ayuda por favor», según cada entrada. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Revisar la secuencia de normalización de la función. 2. Ejecutar los diez casos parametrizados. 3. Comparar cada cadena devuelta con su salida exacta esperada. |
| Ramas y condiciones evaluadas | Conversión a minúsculas; eliminación de tildes y puntuación; traducción de jerga y errores frecuentes. |
| Resultado obtenido | Exitoso. Los diez casos de normalización aprobaron sus comparaciones exactas. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 10. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_nlp.py::test_preprocesamiento_y_jerga |

## CB-02 Selección de campos de consulta

DESCRIPCIÓN DE PRUEBAS DE CAJA BLANCA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-05 - Consulta separada de requisitos costo y plazo |
| Módulo/Área Funcional/Subproceso | NLP / interpretación de costo y plazo |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-05 |
| Descripción del requisito | La detección de subintenciones debe distinguir solicitudes de plazo, costo y textos que no piden esos datos. |
| Código de prueba | CB-02 |
| Caso de prueba | Selección de campos de consulta |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | backend/nlp/preprocesamiento.py: detectar_campos_consulta y detectar_subintencion_directa. |
| Datos de entrada/Acciones de entrada | «cuantos dias demora»; «cual es el horario de atencion de mesa de partes»; consulta de plazo de T_023. |
| Resultado esperado | La primera entrada se interpreta como plazo; horario no activa plazo; la consulta de plazo de T_023 no añade costo. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Identificar las condiciones léxicas de cada campo. 2. Ejecutar las consultas positivas y los fragmentos sin subintención. 3. Comprobar la respuesta de plazo sin precio adicional. |
| Ramas y condiciones evaluadas | Detección positiva de plazo; ausencia de coincidencias; prioridad del plazo sobre una interpretación genérica de costo. |
| Resultado obtenido | Exitoso. Se verificó plazo en la consulta de duración, ausencia de subintención para horario y separación del costo. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 8. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_nlp.py::test_regla_costo_vs_plazo; tests/test_nlp.py::test_regla_horario_no_activa_plazo; tests/test_conversacion_ciudadana.py::test_fragmentos_no_activan_costo_o_plazo; tests/test_respuestas_claras.py::test_nombre_y_valor_explicitos |

## CB-03 Resolución estricta de intenciones macro

DESCRIPCIÓN DE PRUEBAS DE CAJA BLANCA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-04 - Desambiguación y resolución controlada |
| Módulo/Área Funcional/Subproceso | NLP / resolver de alternativas |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-04 |
| Descripción del requisito | El resolver estricto debe resolver una única coincidencia y conservar la ambigüedad cuando no exista una elección inequívoca. |
| Código de prueba | CB-03 |
| Caso de prueba | Resolución estricta de intenciones macro |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | backend/nlp/clasificador.py: coincidencias_intencion_macro y resolver_intencion_macro. |
| Datos de entrada/Acciones de entrada | 925 frases de 185 alternativas; consultas ambiguas de matrimonio; luz/luces; lotes/sublotes; otro/otra; error «subdividr». |
| Resultado esperado | Las 925 frases resuelven su opción esperada; las entradas ambiguas permanecen sin resolución; no se invoca difflib en modo estricto. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Revisar las ramas de selección explícita, coincidencia única y ambigüedad. 2. Ejecutar las frases de todas las alternativas. 3. Bloquear difflib mediante un control de prueba y verificar que el resolver estricto no lo utilice. |
| Ramas y condiciones evaluadas | Cero coincidencias; coincidencia única; varias coincidencias; límites de palabra; desactivación de similitud difusa. |
| Resultado obtenido | Exitoso. Aprobaron las 925 resoluciones y las comprobaciones de ambigüedad y límites de palabra sin difflib. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 926. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_macros_dialogo.py::test_cada_opcion_con_resolver_real; tests/test_macros_dialogo.py::test_ambiguedad_y_limites_sin_difflib |

## CB-04 Acumulación de atributos en varios turnos

DESCRIPCIÓN DE PRUEBAS DE CAJA BLANCA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-06 - Continuidad y rectificación de la conversación |
| Módulo/Área Funcional/Subproceso | Motor de diálogo / estado del caso |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-06 |
| Descripción del requisito | comprender debe acumular los datos compatibles y reducir los candidatos sin elegir por orden. |
| Código de prueba | CB-04 |
| Caso de prueba | Acumulación de atributos en varios turnos |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | backend/chatbot/entendimiento.py: comprender y filtrar. |
| Datos de entrada/Acciones de entrada | Matrimonio: «fuera del local», «dentro del distrito», «en un salón». |
| Resultado esperado | Candidatos b/d/e; después b/e; finalmente opción b, local público dentro del distrito. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Crear el marco de matrimonio sin atributos. 2. Aplicar las tres entradas sucesivamente al mismo marco. 3. Comprobar candidatos intermedios y opción final. |
| Ramas y condiciones evaluadas | Inicialización del marco; actualización de atributos; filtrado parcial; resolución por un único candidato. |
| Resultado obtenido | Exitoso. Los candidatos fueron b/d/e y b/e; la tercera entrada resolvió la opción b. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 1. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_dialogo_natural.py::test_comprension_acumula_atributos_sin_elegir_por_azar |

## CB-05 Comparadores numéricos y condiciones especiales

DESCRIPCIÓN DE PRUEBAS DE CAJA BLANCA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-04 - Desambiguación y resolución controlada |
| Módulo/Área Funcional/Subproceso | Motor de diálogo / clasificación de obras |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-04 |
| Descripción del requisito | Los límites de área o pisos deben conservar su sentido y respetar las condiciones explícitas del proyecto. |
| Código de prueba | CB-05 |
| Caso de prueba | Comparadores numéricos y condiciones especiales |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | backend/chatbot/entendimiento.py: extraer_atributos y comprender. |
| Datos de entrada/Acciones de entrada | Demolición de más de cinco pisos, dos pisos con explosivos, dos pisos con sótano, demolición parcial; mercado con más de 1000 m² y luego 16000. |
| Resultado esperado | T_141, T_141, T_123 y T_121 respectivamente. Para el mercado se pide precisión y después se resuelve T_151. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Revisar la extracción del comparador «mayor». 2. Ejecutar las cuatro variantes de demolición. 3. Probar el límite inferior insuficiente del mercado y aportar el área concreta. |
| Ramas y condiciones evaluadas | Mayor que el límite; área insuficiente para decidir; prioridad de explosivos, sótano y alcance parcial. |
| Resultado obtenido | Exitoso. Las cuatro demoliciones y la aclaración de área del mercado produjeron los resultados esperados. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 5. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_contexto_catalogo.py::test_medidas_no_anulan_condiciones_especiales; tests/test_contexto_catalogo.py::test_limite_inferior_no_equivale_a_medida_exacta |

## CB-06 Valores frontera de confianza del clasificador

DESCRIPCIÓN DE PRUEBAS DE CAJA BLANCA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-04 - Desambiguación y resolución controlada |
| Módulo/Área Funcional/Subproceso | Motor de diálogo / política de decisión |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-04 |
| Descripción del requisito | Las decisiones de confianza deben comparar los valores originales sin redondearlos antes de decidir. |
| Código de prueba | CB-06 |
| Caso de prueba | Valores frontera de confianza del clasificador |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | backend/chatbot/dialogo.py: procesar_mensaje_chat; umbrales de config.py. |
| Datos de entrada/Acciones de entrada | Confianzas controladas: 0.3499, 0.35, 0.5399, 0.54, 0.5499, 0.695, 0.6999 y 0.70; intención T_003. |
| Resultado esperado | Estados: fallback, clarification, clarification, fallback, fallback, fallback, fallback y success, respectivamente. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Sustituir temporalmente la predicción por intención y confianza controladas. 2. Desactivar solo en esta prueba la corroboración léxica independiente. 3. Ejecutar los ocho valores y contrastar los estados. |
| Ramas y condiciones evaluadas | Confianza <0.35; intervalo [0.35,0.54); intervalo [0.54,0.70); confianza >=0.70. |
| Resultado obtenido | Exitoso. Los ocho valores frontera devolvieron los estados esperados sin redondeo previo. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 8. |
| Observaciones | Se aísla la política de confianza de ML. La recuperación contextual o léxica tiene pruebas separadas; esto no mide la exactitud del modelo. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_conversacion_ciudadana.py::test_umbrales_sin_redondear |

## CB-07 Confirmación de una paráfrasis recuperada

DESCRIPCIÓN DE PRUEBAS DE CAJA BLANCA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-04 - Desambiguación y resolución controlada |
| Módulo/Área Funcional/Subproceso | Recuperación de alternativas |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-04 |
| Descripción del requisito | La recuperación por similitud debe proponer una confirmación antes de mostrar datos de un trámite. |
| Código de prueba | CB-07 |
| Caso de prueba | Confirmación de una paráfrasis recuperada |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | backend/chatbot/recuperacion.py: proponer; entendimiento.py y dialogo.py. |
| Datos de entrada/Acciones de entrada | Macro de lotes activa; «los lotes quiero que terminen fusionados»; después «sí, eso quiero». |
| Resultado esperado | El resolver estricto no encuentra coincidencia. Se guarda propuesta b sin datosTramite; la confirmación resuelve T_061. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Desactivar el sugeridor semántico para aislar la recuperación léxica. 2. Comprobar la ausencia de coincidencia estricta. 3. Revisar propuesta y datos antes de confirmar. 4. Confirmar y verificar T_061. |
| Ramas y condiciones evaluadas | Ausencia de coincidencia estricta; propuesta léxica; espera de confirmación; confirmación positiva. |
| Resultado obtenido | Exitoso. Se guardó propuesta b sin entregar ficha; la confirmación posterior resolvió T_061. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 1. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_contexto_catalogo.py::test_indice_lexico_solo_propone_nunca_resuelve |

## CB-08 Aislamiento y limpieza del estado de sesión

DESCRIPCIÓN DE PRUEBAS DE CAJA BLANCA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-11 - Gestión del contexto de sesión |
| Módulo/Área Funcional/Subproceso | Sesiones conversacionales |
| Tipo de requisito | Funcional |
| Código del requisito | R-ANX-11 |
| Descripción del requisito | Cada sesión debe mantener su propio trámite y eliminar el contexto activo cuando se cancela una consulta. |
| Código de prueba | CB-08 |
| Caso de prueba | Aislamiento y limpieza del estado de sesión |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | backend/chatbot/dialogo.py: gestión de tramite_actual, macro_pendiente y cancelaciones. |
| Datos de entrada/Acciones de entrada | Cliente A activa T_015; cliente B pregunta costo sin contexto. En otra sesión se inicia «licencia» y se envía «cancelar». |
| Resultado esperado | B no hereda T_015 de A; A conserva T_015. Tras cancelar no existen macro_pendiente ni tramite_actual. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Abrir dos clientes independientes. 2. Consultar T_015 en el primero y un costo en el segundo. 3. Comprobar la independencia del seguimiento. 4. Cancelar una macro y revisar la eliminación de las claves activas. |
| Ramas y condiciones evaluadas | Sesión con trámite; sesión sin trámite; cancelación y limpieza de estado. |
| Resultado obtenido | Exitoso. Se verificaron sesiones independientes y la eliminación de las claves de contexto después de cancelar. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 2. |
| Observaciones | No se observaron diferencias respecto al resultado esperado en los escenarios ejecutados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_conversacion_ciudadana.py::test_sesiones_independientes; tests/test_conversacion_ciudadana.py::test_macro_permite_cambiar_tema_y_cancelar |

## CB-09 Hash de contraseña y control del rol administrativo

DESCRIPCIÓN DE PRUEBAS DE CAJA BLANCA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-12 - Autenticación y control administrativo |
| Módulo/Área Funcional/Subproceso | Seguridad de la administración |
| Tipo de requisito | No funcional |
| Código del requisito | R-ANX-12 |
| Descripción del requisito | La autenticación debe validar un hash seguro y denegar el acceso a cuentas sin rol administrativo. |
| Código de prueba | CB-09 |
| Caso de prueba | Hash de contraseña y control del rol administrativo |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | backend/admin/routes.py: admin_login; backend/admin/seguridad.py: es_administrador. |
| Datos de entrada/Acciones de entrada | Cuenta admin temporal con hash scrypt; cuenta temporal sin rol Administrador; credenciales correctas para cada cuenta. |
| Resultado esperado | El hash no equivale a la contraseña en claro y check_password_hash lo valida. La cuenta sin rol recibe HTTP 403 y no obtiene acceso a la API. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Inspeccionar el hash almacenado de la cuenta de pruebas. 2. Verificar algoritmo y validación con Werkzeug. 3. Asignar a otra cuenta temporal un rol no administrativo. 4. Intentar iniciar sesión y acceder a trámites. |
| Ramas y condiciones evaluadas | Validación del hash; cuenta sin rol administrativo; denegación del acceso. |
| Resultado obtenido | Exitoso. Se comprobó hash scrypt válido y distinto del texto plano; la cuenta sin rol fue rechazada y no obtuvo autorización. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 2. |
| Observaciones | Se verifica hashing de contraseñas, no cifrado reversible. No se imprimen contraseñas ni hashes completos. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_admin.py::test_password_hash_no_es_texto_plano; tests/test_admin.py::test_usuario_sin_rol_administrativo_no_inicia_sesion |

## CB-10 Tratamiento de excepciones de persistencia

DESCRIPCIÓN DE PRUEBAS DE CAJA BLANCA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-15 - Tratamiento controlado de errores |
| Módulo/Área Funcional/Subproceso | Administración y auditoría |
| Tipo de requisito | No funcional |
| Código del requisito | R-ANX-15 |
| Descripción del requisito | Las excepciones deben producir respuestas controladas sin exponer detalles técnicos ni interrumpir innecesariamente el chat. |
| Código de prueba | CB-10 |
| Caso de prueba | Tratamiento de excepciones de persistencia |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | backend/admin/routes.py: manejo except; backend/chatbot/conversaciones.py: registrar_conversacion. |
| Datos de entrada/Acciones de entrada | Excepciones controladas en consultas administrativas y commit de auditoría; saludo ciudadano durante el fallo simulado. |
| Resultado esperado | Administración: HTTP 500 con mensaje genérico, sin OperationalError. Login: HTTP 503. Fallo de auditoría: el saludo conserva HTTP 200. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Inyectar excepciones mediante monkeypatch en las operaciones previstas. 2. Ejecutar lectura y escritura administrativa y el inicio de sesión. 3. Comprobar la omisión de detalles internos en los mensajes. 4. Simular el fallo de commit de auditoría y enviar un saludo. |
| Ramas y condiciones evaluadas | Captura de excepción; mensaje genérico; rollback de auditoría y continuidad de la respuesta. |
| Resultado obtenido | Exitoso. Se verificaron HTTP 500/503 controlados y HTTP 200 para el saludo pese al fallo simulado de auditoría. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 3. |
| Observaciones | Las excepciones son simuladas en pruebas. No se detuvo MySQL ni se deduce un porcentaje de disponibilidad productiva. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_admin.py::test_admin_error_bd_no_expone_excepcion; tests/test_admin.py::test_admin_login_con_bd_caida_devuelve_503; tests/test_log.py::test_log_falla_no_interrumpe_respuesta_ciudadano |

## CB-11 Anonimización previa al registro de conversaciones

DESCRIPCIÓN DE PRUEBAS DE CAJA BLANCA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-14 - Auditoría y consulta de conversaciones |
| Módulo/Área Funcional/Subproceso | Auditoría y privacidad |
| Tipo de requisito | No funcional |
| Código del requisito | R-ANX-14 |
| Descripción del requisito | La auditoría debe anonimizar identificadores frecuentes, limitar el mensaje y utilizar un identificador de sesión no expuesto en claro. |
| Código de prueba | CB-11 |
| Caso de prueba | Anonimización previa al registro de conversaciones |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | backend/chatbot/conversaciones.py: anonimizar_mensaje y obtener_sesion_id_anonimo. |
| Datos de entrada/Acciones de entrada | DNI 12345678, RUC 20123456789, teléfono +51 987 654 321, correo vecino@example.com y mensaje de más de 500 caracteres. |
| Resultado esperado | Sustitución por [DOCUMENTO], [TELEFONO] y [CORREO]; mensaje <=500 caracteres; identificador hexadecimal de 64 caracteres. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Revisar el orden de anonimización anterior a la persistencia. 2. Enviar los datos sintéticos de prueba. 3. Consultar el registro temporal y comprobar que no contiene los valores originales. 4. Verificar longitud de mensaje e identificador de sesión. |
| Ramas y condiciones evaluadas | Patrón de correo; teléfono; documento; truncamiento del mensaje; generación del identificador de sesión. |
| Resultado obtenido | Exitoso. Los identificadores originales no se conservaron en el mensaje registrado; se verificaron los marcadores y límites previstos. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 2. |
| Observaciones | Los valores de entrada son sintéticos. La prueba se limita a los patrones de anonimización implementados. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_conversacion_ciudadana.py::test_anonimizacion_antes_de_persistir; tests/test_log.py::test_log_campos_correctos_y_anonimizacion |

## CB-12 Límite de intentos de autenticación

DESCRIPCIÓN DE PRUEBAS DE CAJA BLANCA

| Campo | Contenido |
|---|---|
| Requisito | R-ANX-12 - Autenticación y control administrativo |
| Módulo/Área Funcional/Subproceso | Seguridad / limitador de acceso |
| Tipo de requisito | No funcional |
| Código del requisito | R-ANX-12 |
| Descripción del requisito | El sistema debe bloquear temporalmente una combinación de usuario e IP después de alcanzar el límite de intentos fallidos. |
| Código de prueba | CB-12 |
| Caso de prueba | Límite de intentos de autenticación |
| Fecha de prueba | 03/11/2026 |
| Funcionalidad/Característica a evaluar | backend/admin/seguridad.py: verificar_bloqueo_login, registrar_intento_fallido y reset_intentos_login. |
| Datos de entrada/Acciones de entrada | Usuario sintético admin_test_lockout con contraseña incorrecta en seis intentos; reinicio del contador y acceso válido de la cuenta de pruebas. |
| Resultado esperado | Intentos 1 a 5: HTTP 401. Intento 6: HTTP 429 con Retry-After positivo. Tras reiniciar, acceso válido HTTP 200. |
| Requerimientos de ambiente de pruebas | Windows, Python 3.14, Flask, Pytest, cliente HTTP y SQLite temporal con el catálogo de 239 trámites. |
| Condiciones/Restricciones | Sesiones y datos de pruebas; no modificar producción. |
| Pasos de la prueba | 1. Limpiar el contador del entorno de prueba. 2. Enviar cinco accesos incorrectos y comprobar HTTP 401. 3. Enviar el sexto intento y revisar HTTP 429 y Retry-After. 4. Reiniciar el contador y comprobar el acceso administrativo válido. |
| Ramas y condiciones evaluadas | Contador bajo el límite; límite alcanzado; bloqueo; reinicio explícito y acceso posterior. |
| Resultado obtenido | Exitoso. Se obtuvieron cinco respuestas 401 y una 429 con Retry-After; el acceso válido tras el reinicio devolvió HTTP 200. |
| Estado actual | Conforme. Instancias automatizadas asociadas aprobadas: 1. |
| Observaciones | La recuperación se verifica mediante reinicio explícito del contador de pruebas; no se afirma haber esperado el vencimiento natural de cinco minutos. |
| Fecha de cambio de estado | No aplica. |
| Observaciones de corrección | No se requieren correcciones adicionales en los escenarios ejecutados. |
| Evidencia automatizada | tests/test_admin.py::test_limite_intentos_login_bloquea_sexto_y_reinicia |

