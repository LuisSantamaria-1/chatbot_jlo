"""Diálogo municipal: contexto explícito y respuestas sustentadas en el catálogo."""

import logging
import random
import re

from flask import jsonify, request, session

from config import UMBRAL_CONFIANZA, UMBRAL_DUDA_MIN, UMBRAL_DUDA_MAX
from backend.models import Tramite
from backend.nlp import clasificador
from backend.chatbot.menus import menu_macro
from backend.chatbot.recuperacion import buscar_catalogo, recuperar_familia
from backend.chatbot.consultas import preparar as preparar_consultas, etiqueta as etiqueta_consulta
from backend.chatbot.redaccion import respuesta_solicitada, pide_explicacion, explicar_concepto, referencia_concepto, objetivo_especifico, matrimonio_ya_celebrado
from backend.chatbot.politica import (
    FUERA_DOMINIO, PRESENTACION, solicitud_completa, fuera_de_ambito, licencia_ambigua,
    menu_categorias, elegir_categoria, detalle_catalogo, huella,
)
from backend.chatbot.entendimiento import (
    comprender, siguiente_pregunta, acto_conversacional, es_alternativa,
    es_continuacion, tema_explicito, normalizar_dialogo, extraer_atributos, es_detalle_del_caso, PERFILES,
    es_rectificacion, evidencia_contextual, tema_refina_contexto, confirmacion_natural,
)
from backend.nlp.preprocesamiento import (
    preprocesar_texto, detectar_campos_consulta, es_seguimiento_contextual,
    detectar_frustracion, es_correccion_de_contexto, interpretar_confirmacion,
)
from backend.chatbot.mensajes import (
    MENSAJES_SALUDO, MENSAJES_DESPEDIDA, MENSAJES_FALLBACK,
)

logger = logging.getLogger(__name__)
_PENDIENTES = ("macro_pendiente", "macro_nivel_pendiente", "macro_grupo_pendiente", "tramite_pendiente", "campos_pendientes", "marco_dialogo", "aclaracion_tramites", "categoria_pendiente", "tipo_licencia_pendiente", "referencia_concepto")
_CORRECCIONES = {"no era eso", "no es eso", "no ese no", "no eso no", "ese no era", "me equivoque", "no me referia a eso"}
_CANCELACIONES = {"cancelar", "cancela", "reiniciar", "empezar de nuevo", "otra consulta", "otro tramite", "olvida lo anterior"}
_AGRADECIMIENTOS = {"gracias", "muchas gracias", "muchisimas gracias", "ok gracias", "listo gracias", "ya gracias", "ah ya gracias", "ah gracias", "gracias pe", "gracias por la ayuda"}


def _limpiar_pendientes():
    for clave in _PENDIENTES:
        session.pop(clave, None)


def _respuesta(status, mensaje, **datos):
    # El front conserva su contrato. Solo hay botones tras resolver un trámite.
    if status != "success":
        datos["opciones"] = []
    else:
        datos.setdefault("opciones", [])
    if status not in {"saludo", "charla_casual"}:
        session["ultimo_acto"] = status
    if status != "fallback":
        session["fallos_consecutivos"] = 0
        session.pop("ultimo_fallback", None)
    return jsonify(status=status, mensaje=mensaje, **datos), 200


def _buscar_explicito(texto):
    """Nombres completos y códigos dan acceso a todo el catálogo, sin inferir datos."""
    codigo = re.search(r"\bt[ _-]?(\d{3})\b", texto)
    if codigo:
        return Tramite.query.filter_by(id_tramite=f"T_{codigo[1]}").first()
    coincidencias = []
    for tramite in Tramite.query.all():
        nombre = preprocesar_texto(tramite.nombre)
        if re.search(rf"(?<!\w){re.escape(nombre)}(?!\w)", texto):
            coincidencias.append((len(nombre), tramite))
    if coincidencias:
        coincidencias.sort(key=lambda item: item[0], reverse=True)
        if len(coincidencias) == 1 or coincidencias[0][0] > coincidencias[1][0]:
            return coincidencias[0][1]
    return None


def _preguntar_macro(clave, confianza=0.0, grupo=None, estado='clarification', prefacio=''):
    session["macro_pendiente"] = clave
    session.pop("tramite_pendiente", None)
    marco = session.get("marco_dialogo") or {"macro": clave, "atributos": {}, "candidatos": list(clasificador.INTENCIONES_MACRO[clave]["opciones"])}
    if marco.get("macro") != clave:
        marco = {"macro": clave, "atributos": {}, "candidatos": list(clasificador.INTENCIONES_MACRO[clave]["opciones"])}
    if grupo:
        letras = clasificador.INTENCIONES_MACRO[clave].get("grupos", {}).get(grupo, {}).get("opciones", [])
        marco["candidatos"] = [k for k in marco["candidatos"] if k in letras] or list(letras)
        marco["grupo"] = grupo
    _, nivel, grupo = menu_macro(clave, grupo or marco.get("grupo"))
    if marco.get("propuesta"):
        etiqueta = clasificador.INTENCIONES_MACRO[clave]["opciones"][marco["propuesta"]]["etiqueta"].lower()
        pregunta = f"Por lo que me cuentas, ¿te refieres a {etiqueta}?"
        campo = "confirmacion"
    else:
        campo, pregunta = siguiente_pregunta(clave, marco)
    if marco.pop("alternativas", False):
        pregunta = "Sí, hay otras alternativas. " + pregunta
    firma = huella(pregunta)
    if marco.get("firma_pregunta") == firma:
        repeticiones = marco.get("repeticiones_pregunta", 0) + 1
        # Repetir una pregunta no convierte la conversación en una lista de
        # letras. La misma estrategia se aplica a las 39 familias del catálogo.
        prefijos = ('Puedes contármelo con tus palabras. ', 'Vamos paso a paso. ',
                    'Me falta distinguir ese detalle para orientarte bien. ')
        pregunta = prefijos[(repeticiones - 1) % len(prefijos)] + pregunta
        marco["repeticiones_pregunta"] = repeticiones
    else:
        marco["repeticiones_pregunta"] = 0
    marco["firma_pregunta"] = firma
    marco["pregunta"] = campo
    session["marco_dialogo"] = marco
    session["ultima_pregunta"] = pregunta
    session["macro_nivel_pendiente"] = nivel
    session["macro_grupo_pendiente"] = grupo
    return _respuesta(estado, prefacio + pregunta, intent='no_seguro_macro' if estado == 'derivacion' else clave,
                      confianza=round(confianza, 4), opciones=[])


def _responder_tramite(tramite, campos=(), intent=None, confianza=1.0, macro=None, opcion=None):
    marco_resuelto = session.get("marco_dialogo", {})
    if session.get("tramite_actual") != tramite.id_tramite:
        session.pop("macro_resuelta", None)
        session.pop("alternativa_revisor", None)
    session["tramite_actual"] = tramite.id_tramite
    _limpiar_pendientes()
    campos = tuple(campos) or ("requisitos",)
    requisitos = [r.descripcion for r in tramite.requisitos]
    datos_opcion = clasificador.INTENCIONES_MACRO[macro]["opciones"][opcion] if macro and opcion else {}
    partes = respuesta_solicitada(tramite, campos, requisitos)
    datos = {"id_tramite": tramite.id_tramite, "nombre": tramite.nombre}
    for campo in campos:
        if campo == "requisitos":
            datos[campo] = requisitos
        elif campo in {"costo", "plazo"}:
            datos[campo] = getattr(tramite, campo)
    if macro:
        atributos = dict(PERFILES.get(macro, {}).get(opcion, {}))
        atributos.update(marco_resuelto.get("atributos", {}) if marco_resuelto.get("macro") == macro else {})
        session["macro_resuelta"] = {"clave": macro, "opcion": opcion, "campos": list(campos), "atributos": atributos,
                                    "pregunta": marco_resuelto.get('pregunta')}
    if datos_opcion.get("id_revisor") and tramite.id_tramite != datos_opcion["id_revisor"]:
        session["alternativa_revisor"] = {"clave": macro, "opcion": opcion, "id_tramite": datos_opcion["id_revisor"]}
        if 'requisitos' in campos:
            partes.append("Si prefieres Revisor Urbano, dímelo.")
    if campos == ('requisitos',):
        partes.append('Puedes preguntarme cuánto cuesta o cuánto demora.')
    cola=session.get('consultas_en_espera',[])
    if cola and not session.get('consulta_multiple_pendiente') and not session.get('recordatorio_consulta'):
        partes.append('También queda pendiente tu consulta sobre '+etiqueta_consulta(cola[0]['macro'])+'. Cuando quieras, dime «continuar con la otra».')
        session['recordatorio_consulta']=True
    session.pop("ultima_pregunta", None)
    session["fallos_consecutivos"] = 0
    return _respuesta("success", "\n\n".join(partes), intent=intent or tramite.id_tramite,
                      confianza=round(confianza, 4), **datos, datosTramite=datos,
                      opciones=[{"texto": "Requisitos", "valor": "¿Qué requisitos piden?"},
                                {"texto": "Costo", "valor": "¿Cuánto cuesta?"},
                                {"texto": "Plazo", "valor": "¿Cuánto demora?"},
                                {"texto": "Otro trámite", "valor": "otro trámite"}])


def _resolver_macro(clave, texto, campos, confianza):
    marco = session.get("marco_dialogo", {})
    if marco.get("propuesta"):
        confirmacion = confirmacion_natural(texto)
        if confirmacion == "si":
            opcion = marco["propuesta"]
        elif confirmacion == "no":
            rechazado = marco.pop("propuesta")
            marco["candidatos"] = [k for k in marco.get("candidatos", []) if k != rechazado]
            marco["rechazadas"] = list(set(marco.get("rechazadas", ())) | {rechazado})
            marco.pop("firma_pregunta", None)
            session["marco_dialogo"] = marco
            if len(preprocesar_texto(texto).split()) <= 2:
                return _preguntar_macro(clave, confianza)
            opcion, marco = comprender(clave, texto, marco)
        else:
            opcion, marco = comprender(clave, texto, marco)
    else:
        opcion, marco = comprender(clave, texto, marco)
    session["marco_dialogo"] = marco
    codigo = None
    if opcion and opcion!='no_seguro' and clave in {'consultar_licencia_funcionamiento','consultar_licencia_cesionario','consultar_itse'} and re.search(r'\b(?:creo|supongo|no estoy segur[oa])\b',normalizar_dialogo(texto)):
        marco['propuesta']=opcion
        session['marco_dialogo']=marco
        return _preguntar_macro(clave,confianza,prefacio='Para confirmar la categoría de la evaluación: ')
    if opcion and opcion != "no_seguro":
        datos_opcion = clasificador.INTENCIONES_MACRO[clave]["opciones"][opcion]
        codigo = datos_opcion.get("id_revisor") if clasificador.solicita_revisor(texto) else None
        codigo = codigo or datos_opcion["id_tramite"]
    if codigo:
        tramite = Tramite.query.filter_by(id_tramite=codigo).first()
        if tramite:
            intent = "resolucion_macro" if session.get("macro_pendiente") == clave else tramite.id_tramite
            return _responder_tramite(tramite, campos, intent=intent, confianza=confianza,
                                      macro=clave, opcion=opcion)
    if opcion is None and campos and set(campos) <= {'costo','plazo'}:
        # Una alternativa con Revisor Urbano puede tener otro costo o plazo.
        # Solo anunciar un valor común si también coincide en esas fichas.
        codigos=list({d[campo_id]
                      for k in marco.get('candidatos',())
                      for d in [clasificador.INTENCIONES_MACRO[clave]['opciones'][k]]
                      for campo_id in ('id_tramite','id_revisor') if d.get(campo_id)})
        fichas=Tramite.query.filter(Tramite.id_tramite.in_(codigos)).all() if codigos else []
        comunes={campo:{(getattr(t,campo) or '').strip() for t in fichas} for campo in campos}
        if len(fichas)>1 and all(len(v)==1 and next(iter(v)).lower() not in {'','no especificado'} for v in comunes.values()):
            datos={k:next(iter(v)) for k,v in comunes.items()}
            asunto=clave.removeprefix('consultar_').replace('_',' ')
            partes=[]
            for campo,valor in datos.items():
                if campo=='costo':
                    partes.append(f'Para las alternativas de {asunto} que estamos viendo, el catálogo indica el mismo costo: {valor}.')
                else:
                    mostrado=f'Inmediato ({valor})' if re.match(r'^0(?:\s|$)',valor) or 'aprobacion automatica' in preprocesar_texto(valor) else valor
                    partes.append(f'Para las alternativas de {asunto} que estamos viendo, el plazo registrado es el mismo: {mostrado}.')
            session['macro_pendiente']=clave
            session['campos_pendientes']=[]
            pregunta=siguiente_pregunta(clave,marco)[1]
            session['ultima_pregunta']=pregunta
            return _respuesta('clarification','\n\n'.join(partes)+'\n\nSi también necesitas los requisitos, seguimos con tu caso. '+pregunta,
                              intent='campos_comunes_macro',confianza=round(confianza,4),**datos)
    if opcion == "no_seguro":
        # La duda conserva el menú y su nivel; no lista instrucciones largas.
        campo, pregunta = siguiente_pregunta(clave, marco)
        if campo == "riesgo":
            codigos = [clasificador.INTENCIONES_MACRO[clave]['opciones'][k]['id_tramite'] for k in marco.get('candidatos', ())]
            fichas = Tramite.query.filter(Tramite.id_tramite.in_(codigos)).all()
            listas = [[r.descripcion for r in t.requisitos] for t in fichas]
            comunes = [r for r in listas[0] if all(r in lista for lista in listas[1:])] if listas else []
            mensaje = 'Sin esa evaluación aún no puedo fijar una categoría ni un costo. La municipalidad puede confirmarla según las características de tu local.'
            if comunes:
                mensaje += '\n\nEstos requisitos aparecen en todas las alternativas que estamos viendo:\n' + '\n'.join('- ' + r for r in comunes)
            mensaje += '\n\nCuando tengas la categoría, seguimos desde aquí. También puedes preguntarme por otro trámite.'
        else:
            return _preguntar_macro(clave, confianza, estado='derivacion', prefacio='No hay problema, vamos paso a paso. ')
        session["ultima_pregunta"] = pregunta
        return _respuesta("derivacion", mensaje, intent="no_seguro_macro", opciones=[])
    return None


def _cortesia(texto):
    acto = acto_conversacional(texto)
    marco = session.get("marco_dialogo", {})
    if not acto or ((marco.get("propuesta") or session.get("tramite_pendiente")) and acto in {"acuse", "negacion"}):
        return None
    if acto in {"acuse", "negacion"} and marco.get("pregunta") in {"iluminacion", "cambios", "separacion", "vigencia", "alcance", "pruebas", "codigo", "fase", "unica", "riesgo"}:
        return None
    anterior = session.get("cortesia_anterior")
    session["cortesia_anterior"] = acto
    pregunta = session.get("ultima_pregunta")
    if acto == "saludo":
        mensaje = "¡Hola! Soy Leonardito. Cuéntame qué necesitas hacer y te voy orientando."
        if session.get("tramite_actual"):
            mensaje = "¡Hola de nuevo! Podemos seguir con lo que estábamos viendo o conversar sobre otro trámite."
        return _respuesta("saludo", mensaje, intent="saludo", confianza=1.0)
    if acto == "bienestar":
        return _respuesta("charla_casual", "¡Bien, gracias por preguntar! Aquí estoy para ayudarte. Cuéntame, ¿qué necesitas resolver hoy?", intent="charla_casual", confianza=1.0)
    if acto == "conversar":
        return _respuesta("charla_casual", "Claro, te escucho. No necesitas conocer el nombre del trámite: cuéntame qué quieres hacer en la municipalidad y vamos paso a paso.", intent="charla_casual", confianza=1.0)
    if acto == "presentacion":
        return _respuesta("charla_casual", PRESENTACION, intent="charla_casual", confianza=1.0)
    if acto == "sin_interes":
        _limpiar_pendientes()
        for clave in ('tramite_actual','macro_resuelta','alternativa_revisor','ultima_pregunta','consultas_en_espera','consulta_multiple_pendiente','recordatorio_consulta'):
            session.pop(clave,None)
        return _respuesta("charla_casual", "Sin problema 😊 Cuando necesites orientación sobre algún trámite, escríbeme.", intent="sin_interes", confianza=1.0)
    if acto == "reiniciar":
        _limpiar_pendientes()
        for k in ('tramite_actual', 'macro_resuelta', 'alternativa_revisor', 'ultima_pregunta', 'consultas_en_espera', 'consulta_multiple_pendiente', 'recordatorio_consulta'):
            session.pop(k, None)
        return _respuesta("correction", "Disculpa, interpreté mal tu consulta. Empecemos de nuevo: cuéntame qué quieres hacer o qué parte necesitas aclarar.", intent="reiniciar_contexto")
    if acto == "agradecimiento":
        return _respuesta("charla_casual", "¡De nada! Aquí sigo si te surge otra duda.", intent="agradecimiento", confianza=1.0)
    if acto == "acuse":
        mensaje = 'Claro, cuéntame qué trámite necesitas o qué quieres hacer en la municipalidad.' if not session.get('tramite_actual') else 'Claro. Puedes seguir preguntándome sobre este trámite o contarme qué otro necesitas.'
        if anterior == acto:
            mensaje = 'Aquí sigo si necesitas algo más.'
        return _respuesta("charla_casual", mensaje, intent="acuse_recibo", confianza=1.0)
    if acto == "negacion":
        mensaje = "Está bien. No tienes que elegir nada ahora; podemos seguir cuando quieras." if anterior != acto else "De acuerdo, aquí estaré."
        return _respuesta("charla_casual", mensaje, intent="negacion_casual", confianza=1.0)
    if acto == "explicacion":
        if pregunta:
            return _respuesta("clarification", "Te lo explico de otra forma: necesito ese dato para darte el trámite y el importe correctos. " + pregunta, intent="explicar_pregunta")
        return _respuesta("charla_casual", "¿Qué parte quieres que te explique? Puedo repasar los requisitos, el costo o el plazo que acabamos de ver.", intent="explicar_respuesta")
    if acto == "despedida":
        _limpiar_pendientes()
        for clave in ("tramite_actual", "macro_resuelta", "alternativa_revisor", "ultima_pregunta", "consultas_en_espera", "consulta_multiple_pendiente", "recordatorio_consulta"):
            session.pop(clave, None)
        return _respuesta("despedida", "¡Hasta pronto! Cuando necesites orientación sobre otro trámite de JLO, aquí estaré.", intent="despedida", confianza=1.0)
    return None


def _grupo_para_menu(clave, texto, grupo_actual=None):
    grupos = clasificador.INTENCIONES_MACRO[clave].get("grupos", {})
    coincidencias = set(clasificador.coincidencias_intencion_macro(clave, texto))
    if len(coincidencias) > 1:
        comunes = [k for k, grupo in grupos.items() if coincidencias <= set(grupo["opciones"])]
        return comunes[0] if len(comunes) == 1 else None
    return clasificador.resolver_grupo_macro(clave, texto) or grupo_actual


def _seguimiento_natural(texto):
    if es_seguimiento_contextual(texto):
        return True
    auxiliares = set("""y el la los las un una de del para por en a al que cual cuales cuanto cuantos
    me mi se es son seria lo le te tu con sin favor porfa ese esa este esta esto eso mismo tramite municipal
    puedes podria podrias decir decirme indicar indicarme saber dime dar dame quiero quisiera deseo necesito conocer
    requisitos requisito documentos documento papeles papelitos piden costo costos cuesta cuestan costaria costara
    precio pago pagar tasa monto valor arancel tarifa cobran cobrar cobren vale sale plazo plazos demora demoran
    tarda tardan duracion tiempo dias cuando entregan estara entonces ahora van voy debo tengo tendria llevar
    presentar piden pedir solicitar resumen resumir repite repetir eso todos todo mas informacion seria cuanto
    demoraria demorarian tardaria tardarian estaria saldria pagaria cobrarian falta hace ahi aqui documentacion""".split())
    auxiliares.update({'gratis','gratuito','gratuita','paga','barato','barata','entregan','tiempo','todo','eso','son'})
    auxiliares.update({'licencia','certificado','permiso','solicitud','demoro','entregado','entregaran','ya'})
    return bool(set(texto.split())) and set(texto.split()) <= auxiliares


def _confirmar_tramite(tramite, campos, confianza):
    session['tramite_pendiente'] = tramite.id_tramite
    session['campos_pendientes'] = list(campos)
    return _respuesta('clarification', f'Quiero asegurarme de entenderte. ¿Te refieres a «{tramite.nombre}»?',
                      intent=tramite.id_tramite, confianza=round(confianza, 4),
                      id_tramite_sugerido=tramite.id_tramite, nombre_sugerido=tramite.nombre, opciones=[])


def _fallback(intent, confianza, texto, campos=()):
    cuenta = min(3, session.get("fallos_consecutivos", 0) + 1)
    session["fallos_consecutivos"] = cuenta
    tema = tema_explicito(texto)
    if tema:
        session["fallos_consecutivos"] = 0
        session["campos_pendientes"] = list(campos or session.get("campos_pendientes", ()))
        resuelta = _resolver_macro(tema, texto, session["campos_pendientes"], confianza)
        if resuelta:
            return resuelta
        return _preguntar_macro(tema, confianza)
    if session.get("macro_pendiente"):
        return _preguntar_macro(session["macro_pendiente"], confianza, session.get("macro_grupo_pendiente"))
    if intent in clasificador.INTENCIONES_MACRO:
        familia = recuperar_familia(texto, preferida=intent)
        if familia:
            session['campos_pendientes'] = list(campos)
            resuelta = _resolver_macro(familia,texto,campos,confianza)
            return resuelta or _preguntar_macro(familia,confianza)
    if intent == 'fuera_de_dominio' and confianza >= UMBRAL_DUDA_MIN:
        session['fallos_consecutivos'] = 0
        return _respuesta('fallback', FUERA_DOMINIO, intent=intent, confianza=round(confianza, 4))
    # Si ML no alcanza el umbral, una recuperación independiente puede pedir
    # confirmación. No se presenta una ficha ni un costo por similitud.
    candidato = buscar_catalogo(texto, [(t.id_tramite, t.nombre) for t in Tramite.query.all()], preferida=intent)
    if candidato:
        tramite = Tramite.query.filter_by(id_tramite=candidato).first()
        if tramite:
            return _confirmar_tramite(tramite, campos, confianza)
    if cuenta == 1:
        mensaje = "Todavía no tengo claro qué necesitas. Cuéntame qué quieres hacer en la municipalidad; no hace falta que sepas el nombre del trámite."
    elif cuenta == 2:
        mensaje = menu_categorias()
        session['categoria_pendiente'] = True
    else:
        mensaje = "Aún no logro distinguir el trámite. Cuéntame para qué lo necesitas y qué ya tienes, y lo revisamos paso a paso. Si tu caso no figura en el catálogo, la municipalidad podrá confirmarlo."
    session['ultimo_fallback'] = huella(normalizar_dialogo(texto))
    return _respuesta("fallback", mensaje, intent=intent, confianza=round(confianza, 4))


def procesar_mensaje_chat():
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or not data:
            return jsonify(status="error", mensaje="No se recibió un cuerpo JSON válido con la llave 'mensaje'."), 400
        mensaje = data.get("mensaje")
        if not isinstance(mensaje, str) or not mensaje.strip():
            return jsonify(status="fallback", mensaje="Por favor, escribe una pregunta sobre el trámite municipal que deseas realizar."), 400
        if len(mensaje) > 2000:
            return jsonify(status="error", mensaje="Escribe tu consulta en un máximo de 2000 caracteres."), 400

        # Separar asuntos completos evita heredar «requisitos del puesto» como
        # si se hubieran pedido junto con el costo del matrimonio.
        if normalizar_dialogo(mensaje) not in _CANCELACIONES and acto_conversacional(mensaje) not in {'despedida','sin_interes','reiniciar'} and not detectar_frustracion(mensaje):
            mensaje_elegido,pregunta_multiple=preparar_consultas(mensaje,session)
            if pregunta_multiple:
                return _respuesta('clarification',pregunta_multiple,intent='consultas_multiples')
            mensaje=mensaje_elegido

        texto_original = preprocesar_texto(mensaje)
        texto = normalizar_dialogo(mensaje)
        campos = detectar_campos_consulta(texto)
        if re.search(r"\b(?:costaria|costara|costarian)\b", texto) and "costo" not in campos:
            campos = ("costo", *campos)
        if re.search(r"\b(?:demoraria|demorarian|tardaria|tardarian)\b", texto) and "plazo" not in campos:
            campos = (*campos, "plazo")
        if re.search(r"\b(?:saldria|pagaria|cobrarian)\b", texto) and "costo" not in campos:
            campos = (*campos, "costo")
        if re.search(r"\b(?:cuanto.*(?:cobrar|vale|pagar)|que.*(?:llevo|presento|debo llevar)|papelitos)\b", texto):
            campo_extra = "costo" if re.search(r"cobrar|vale|pagar", texto) else "requisitos"
            if campo_extra not in campos:
                campos = (*campos, campo_extra)
        if detectar_frustracion(texto_original) or texto_original in {"tmr", "ptm", "pucha", "que vaina"}:
            pregunta = session.get("ultima_pregunta")
            if session.get("tramite_actual") and not session.get('macro_pendiente'):
                _limpiar_pendientes()
                mensaje_empatia = "Entiendo tu molestia. Si la información no corresponde a tu caso, cuéntame qué quieres cambiar y lo revisamos paso a paso."
            else:
                mensaje_empatia = "Te entiendo, vamos con calma. " + (pregunta or "Cuéntame qué quieres conseguir con tu trámite y buscamos cómo orientarte.")
            return _respuesta("frustration", mensaje_empatia, intent="frustracion")
        if texto in _CANCELACIONES:
            _limpiar_pendientes()
            for k in ('consultas_en_espera','consulta_multiple_pendiente','recordatorio_consulta'):
                session.pop(k,None)
            session.pop("tramite_actual", None)
            session.pop("macro_resuelta", None)
            session.pop("alternativa_revisor", None)
            return _respuesta("correction", "Claro, empezamos otra consulta. ¿Qué trámite de la Municipalidad de José Leonardo Ortiz necesitas?", intent="reiniciar_contexto")
        if texto in {'quiero un tramite','necesito un tramite','quiero hacer un tramite'}:
            _limpiar_pendientes()
            for k in ('tramite_actual','macro_resuelta','alternativa_revisor','ultima_pregunta'):
                session.pop(k,None)
            return _respuesta('clarification','Claro. Cuéntame qué quieres hacer en la municipalidad; por ejemplo, abrir un negocio, gestionar tu terreno o pedir un documento.',intent='consulta_general')
        if texto in _CORRECCIONES:
            resuelta = session.get("macro_resuelta", {})
            clave = session.get("macro_pendiente") or resuelta.get("clave")
            if clave in clasificador.INTENCIONES_MACRO:
                _limpiar_pendientes()
                session.pop("tramite_actual", None)
                session.pop("alternativa_revisor", None)
                session["campos_pendientes"] = resuelta.get("campos", [])
                return _preguntar_macro(clave)
        if pide_explicacion(texto):
            marco = session.get('marco_dialogo', {})
            explicacion = explicar_concepto(texto, marco.get('pregunta'))
            if explicacion:
                referencia=referencia_concepto(texto)
                if referencia:
                    _limpiar_pendientes()
                    for k in ('tramite_actual','macro_resuelta','alternativa_revisor'):
                        session.pop(k,None)
                    session['referencia_concepto']=referencia
                    if referencia.get('macro'):
                        clave=referencia['macro']
                        session['macro_pendiente']=clave
                        _,marco=comprender(clave,'')
                        session['marco_dialogo']=marco
                        pregunta=siguiente_pregunta(clave,marco)[1]
                        session['ultima_pregunta']=pregunta
                        return _respuesta('clarification',explicacion+'\n\n'+pregunta,intent='explicar_concepto')
                    return _respuesta('charla_casual',explicacion,intent='explicar_concepto')
                if 'divorcio ulterior' in texto:
                    ficha = Tramite.query.filter_by(id_tramite='T_034').first()
                    notas = [r.descripcion for r in ficha.requisitos if preprocesar_texto(r.descripcion).startswith('nota')] if ficha else []
                    if notas:
                        explicacion += '\n\nLo que indica el catálogo: ' + ' '.join(notas)
                if session.get('macro_pendiente'):
                    pregunta = siguiente_pregunta(session['macro_pendiente'], marco)[1]
                    session['ultima_pregunta'] = pregunta
                    return _respuesta('clarification', explicacion + '\n\n' + pregunta, intent='explicar_concepto')
                return _respuesta('charla_casual', explicacion, intent='explicar_concepto')
            return _respuesta('clarification', 'Claro. Dime qué palabra o qué parte del trámite quieres que te explique.', intent='explicar_concepto')
        if matrimonio_ya_celebrado(texto):
            _limpiar_pendientes()
            for clave in ('tramite_actual', 'macro_resuelta', 'alternativa_revisor'):
                session.pop(clave, None)
            return _respuesta('derivacion', 'En el catálogo que manejo no figura qué debes presentar en tu distrito después de casarte en otro. Confírmalo directamente con la municipalidad. Si necesitas algún documento o trámite del catálogo, cuéntame cuál.', intent='consulta_no_registrada')
        cortesia = _cortesia(texto)
        if cortesia:
            return cortesia
        session.pop("cortesia_anterior", None)
        fuera = fuera_de_ambito(texto)
        if fuera:
            session['fallos_consecutivos'] = 0
            return _respuesta('fallback', fuera, intent='fuera_de_dominio')
        referencia=session.get('referencia_concepto',{})
        if referencia.get('id_tramite') and campos and _seguimiento_natural(texto):
            ficha=Tramite.query.filter_by(id_tramite=referencia['id_tramite']).first()
            if ficha:
                return _responder_tramite(ficha,campos)
        if licencia_ambigua(texto) or (not session.get('tramite_actual') and not session.get('macro_pendiente') and campos and re.search(r'\blicencia\b',texto) and _seguimiento_natural(texto) and not tema_explicito(texto)):
            _limpiar_pendientes()
            session['tipo_licencia_pendiente'] = True
            return _respuesta('clarification', '¿La licencia es para abrir un negocio, para una construcción o para otra actividad? Cuéntame qué quieres hacer.', intent='tipo_licencia', opciones=[])
        if session.get('tipo_licencia_pendiente'):
            elegida = {'a': 'consultar_licencia_funcionamiento', 'b': 'consultar_licencia_construccion'}.get(texto)
            if elegida:
                _limpiar_pendientes()
                return _preguntar_macro(elegida)
            session.pop('tipo_licencia_pendiente', None)
        if session.get('categoria_pendiente'):
            categoria = elegir_categoria(texto)
            if categoria and (texto.isdigit() or len(texto.split()) <= 4):
                _limpiar_pendientes()
                ayudas = {
                    '1': '¿Quieres abrir un negocio, cambiar su licencia, transferirla o cerrarlo? Cuéntame qué negocio es.',
                    '2': '¿Quieres construir, ampliar, remodelar, demoler o dividir/habilitar un terreno?',
                    '3': '¿Qué necesitas acreditar con el documento: numeración, posesión, catastro u otra cosa?',
                    '4': '¿Quieres casarte, separarte o continuar un divorcio?',
                    '5': '¿Quieres registrar a tu perro? Cuéntame su raza para orientarte.',
                    '6': '¿Es para registrar tu mototaxi, renovar su tarjeta, cambiar datos o gestionar una flota?',
                    '7': '¿Quieres conseguir un puesto, renovarlo o hacer algún cambio en tu puesto del mercado?',
                    '8': 'Cuéntame qué quieres conseguir en la municipalidad y buscamos el trámite.',
                }
                return _respuesta('clarification', ayudas[categoria], intent='categoria_' + categoria, opciones=[])
        aclaracion=session.get('aclaracion_tramites')
        tema_aclaracion=tema_explicito(texto)
        familia_aclaracion={'titular_local':'consultar_gestion_licencia', 'certificado_sanitario':'consultar_certificacion_sanitaria'}.get(aclaracion)
        eleccion_licencia=(aclaracion=='titular_local' and tema_aclaracion=='consultar_licencia_funcionamiento'
                          and not campos and not extraer_atributos(texto,tema_aclaracion)
                          and not re.search(r'\b(?:abrir|apertura|sacar|obtener)\b',texto))
        if familia_aclaracion and tema_aclaracion and tema_aclaracion != familia_aclaracion and not eleccion_licencia:
            _limpiar_pendientes()
            aclaracion=None
        if aclaracion in {'titular_local','certificado_sanitario'}:
            codigo=None
            if aclaracion=='titular_local' and re.search(r'\b(?:licencia|negocio|funcionamiento)\b',texto):
                codigo='T_004'
            elif aclaracion=='certificado_sanitario' and re.search(r'\b(?:local|restaurante|establecimiento|negocio|certificado)\b',texto):
                codigo='T_028'
            if codigo:
                ficha=Tramite.query.filter_by(id_tramite=codigo).first()
                if ficha:
                    return _responder_tramite(ficha,campos or session.get('campos_pendientes',()))
            if re.search(r'\b(?:propiedad|propietario|personal|persona|manipular)\b',texto):
                _limpiar_pendientes()
                session.pop('tramite_actual',None)
                return _respuesta('derivacion','Ese caso es distinto del trámite del establecimiento que tengo registrado. Confirma el documento y el canal correspondiente con la municipalidad; no voy a presentarte una ficha como si fuera equivalente.',intent='consulta_no_registrada')
        if re.search(r'\b(?:compre|comprado)\b.*\b(?:local|negocio)\b',texto) and re.search(r'\b(?:mi nombre|ponerlo a mi nombre)\b',texto) and not re.search(r'\blicencia\b',texto):
            _limpiar_pendientes()
            for k in ('tramite_actual','macro_resuelta','alternativa_revisor'):
                session.pop(k,None)
            session['aclaracion_tramites']='titular_local'
            session['campos_pendientes']=list(campos)
            return _respuesta('clarification','¿Quieres transferir la licencia de funcionamiento del negocio o cambiar la propiedad del local? Son gestiones diferentes; dime a cuál te refieres.',intent='aclarar_titular_local')
        if 'carnet sanitario' in texto:
            _limpiar_pendientes()
            session['aclaracion_tramites']='certificado_sanitario'
            session['campos_pendientes']=list(campos)
            session.pop('tramite_actual',None)
            return _respuesta('clarification','En el catálogo tengo la certificación sanitaria del establecimiento. ¿Te refieres a ese documento del restaurante o a un carnet personal para manipular alimentos?',intent='aclarar_certificacion_sanitaria')
        if session.get('tramite_actual') and not session.get('macro_pendiente') and detalle_catalogo(texto):
            actual = Tramite.query.filter_by(id_tramite=session['tramite_actual']).first()
            if actual:
                notas = [r.descripcion for r in actual.requisitos if re.search(r'\b(?:nota|solo procede|siempre que|hasta|despues de)\b', preprocesar_texto(r.descripcion))]
                detalle = '\n'.join(notas) if notas else f'Nombre registrado: {actual.nombre}.'
                return _respuesta('derivacion', 'El catálogo indica lo siguiente para este trámite:\n' + detalle + '\n\nNo registra una respuesta más específica a ese supuesto. Confirma tu caso con la municipalidad antes de iniciar el trámite.', intent='detalle_tramite_actual')
        if not texto:
            return _respuesta("fallback", random.choice(MENSAJES_FALLBACK), intent="fuera_de_dominio", confianza=0.0)
        if clasificador.modelo_nlp is None and clasificador.cargar_modelo() is None:
            return jsonify(status="error", mensaje="El modelo de procesamiento de lenguaje natural no está disponible en el servidor."), 503

        # El pipeline debe recibir el mismo preprocesamiento que en el
        # entrenamiento. Los alias conversacionales se usan para los slots.
        intent, confianza = clasificador.predecir_intencion(texto_original)
        # No se registran consultas ciudadanas en claro en el log de aplicación.
        logger.info("Intent: %s | Confianza: %.4f | Trámite activo: %s", intent, confianza, session.get("tramite_actual"))
        macro = session.get("macro_pendiente")
        if macro not in clasificador.INTENCIONES_MACRO:
            macro = None
        # Las letras explícitas pertenecen al diálogo, no al clasificador ML.
        if macro and clasificador.interpretar_seleccion_macro(macro, texto):
            resuelta = _resolver_macro(macro, mensaje, session.get("campos_pendientes", ()), confianza)
            if resuelta:
                return resuelta
        alternativa = session.get("alternativa_revisor")
        if alternativa and clasificador.solicita_revisor(texto) and re.fullmatch(r"(?:(?:si|mejor|prefiero|quiero|con|un|por|favor|el|evaluacion|de|que|sea|urbano|urbanos|revisor|revisores)\s*)+", texto):
            return _resolver_macro(alternativa["clave"], alternativa["opcion"] + " con revisor", campos, confianza)
        codigo_objetivo = objetivo_especifico(texto, macro or session.get('macro_resuelta', {}).get('clave'))
        if codigo_objetivo:
            tramite = Tramite.query.filter_by(id_tramite=codigo_objetivo).first()
            if tramite:
                campos_objetivo = campos or (tuple(session.get('campos_pendientes', ())) if macro == 'consultar_matrimonio_civil' else ())
                return _responder_tramite(tramite, campos_objetivo, confianza=confianza)
        explicito = _buscar_explicito(texto_original)
        if explicito:
            # "Ampliación de plazo" es el nombre del trámite, no una
            # pregunta por su duración. Interpretar solo lo que lo acompaña.
            nombre = preprocesar_texto(explicito.nombre)
            consulta = re.sub(rf"(?<!\w){re.escape(nombre)}(?!\w)", "", texto_original)
            campos_explicitos = detectar_campos_consulta(consulta) or tuple(session.get("campos_pendientes", ()))
            return _responder_tramite(explicito, campos_explicitos, confianza=1.0)
        if re.search(r"\bt[ _-]?\d{3}\b", texto):
            return _respuesta("fallback", "No encuentro ese código en el catálogo municipal. Revisa el código o dime el nombre del trámite.", intent="tramite_no_encontrado")

        if session.get("aclaracion_tramites") == "planos_servicios":
            codigo = None
            if re.search(r"\b(?:agua|luz|servicios|medidor|posesion)\b", texto):
                codigo = "T_031"
            elif re.search(r"\b(?:prescripcion|adquisitiva|linderos|rectificar|rectificacion|supletorio)\b", texto):
                codigo = "T_008"
            if codigo:
                tramite = Tramite.query.filter_by(id_tramite=codigo).first()
                if tramite:
                    return _responder_tramite(tramite, campos or session.get("campos_pendientes", ()))

        # Arbitrar la intención ANTES de consultar la propuesta o los slots
        # pendientes. La misma regla se aplica a todas las macros registradas.
        tema = tema_explicito(texto)
        completa = solicitud_completa(texto) and not _seguimiento_natural(texto)
        contexto = macro or session.get('macro_resuelta', {}).get('clave')
        pregunta_previa = session.get('marco_dialogo', {}).get('pregunta') if macro else session.get('macro_resuelta', {}).get('pregunta')
        detalle_contextual = bool(contexto and evidencia_contextual(texto, contexto, pregunta_previa))
        compatible = bool(contexto and tema_refina_contexto(tema, contexto, texto))
        rectificacion = bool(contexto and es_rectificacion(texto) and compatible)
        anterior_resuelto=session.get('macro_resuelta',{})
        if not macro and contexto and campos and tema==contexto and not completa and session.get('tramite_actual'):
            nuevos=extraer_atributos(texto,contexto,pregunta_previa)
            previos=anterior_resuelto.get('atributos',{})
            if all(k in previos and v==previos[k] for k,v in nuevos.items()):
                ficha=Tramite.query.filter_by(id_tramite=session['tramite_actual']).first()
                if ficha:
                    return _responder_tramite(ficha,campos,confianza=confianza)
        # Sin un objeto nuevo explícito, una respuesta reconocible pertenece a
        # la pregunta anterior, aunque empiece con «quiero» o tenga muchas palabras.
        nueva_peticion_individual=bool(contexto and completa and str(intent).startswith('T_') and confianza >= UMBRAL_CONFIANZA
                                      and not extraer_atributos(texto,contexto,pregunta_previa))
        if rectificacion or (detalle_contextual and compatible and tema != contexto and not nueva_peticion_individual):
            completa = False
            tema = contexto
        if tema and str(intent).startswith('T_') and confianza >= UMBRAL_DUDA_MIN and not (detalle_contextual and not completa):
            opciones_tema = clasificador.INTENCIONES_MACRO[tema]['opciones'].values()
            ids_tema = {d['id_tramite'] for d in opciones_tema} | {d['id_revisor'] for d in opciones_tema if d.get('id_revisor')}
            if intent not in ids_tema:
                # Un procedimiento específico (p. ej. postergar una boda)
                # prevalece sobre detectar solamente su familia «matrimonio».
                tramite = Tramite.query.filter_by(id_tramite=intent).first()
                if tramite:
                    return (_responder_tramite(tramite, campos, confianza=confianza) if confianza >= UMBRAL_CONFIANZA
                            else _confirmar_tramite(tramite, campos, confianza))
        destino = tema
        marco_previo = session.get('marco_dialogo', {})
        respuesta_slot = (detalle_contextual or rectificacion) and not completa
        if not destino and macro and intent in clasificador.INTENCIONES_MACRO and intent != macro and confianza >= UMBRAL_CONFIANZA and not respuesta_slot:
            destino = intent
        if not destino and completa and intent in clasificador.INTENCIONES_MACRO and confianza >= UMBRAL_DUDA_MIN:
            destino = intent
        if respuesta_slot and compatible:
            destino = contexto
        if destino and (completa or not contexto or destino != contexto):
            _limpiar_pendientes()
            session.pop('macro_resuelta', None)
            session.pop('alternativa_revisor', None)
            session.pop('tramite_actual', None)
            session['campos_pendientes'] = list(campos)
            resuelta = _resolver_macro(destino, mensaje, campos, confianza)
            return resuelta or _preguntar_macro(destino, confianza, _grupo_para_menu(destino, texto))
        if completa:
            _limpiar_pendientes()
            session.pop('macro_resuelta', None)
            session.pop('tramite_actual', None)
            macro = None

        # Un cambio de modalidad se entiende dentro del asunto ya resuelto.
        # No exigir que el ciudadano repita "matrimonio", "licencia", etc.
        anterior = session.get("macro_resuelta", {})
        if not macro and anterior.get("clave") and (not tema or tema == anterior["clave"]):
            clave = anterior["clave"]
            nuevos = extraer_atributos(texto, clave, anterior.get('pregunta'))
            if es_alternativa(texto) or ((nuevos or detalle_contextual or rectificacion or es_continuacion(texto, clave)) and not _seguimiento_natural(texto)):
                if not (intent == "fuera_de_dominio" and confianza >= UMBRAL_CONFIANZA and not nuevos and not es_alternativa(texto)):
                    grupo_nuevo=clasificador.resolver_grupo_macro(clave,texto)
                    reinicia_grupo=grupo_nuevo and not nuevos and not campos
                    atributos_previos = {} if reinicia_grupo or re.search(r"\b(?:otro|otra|diferente|distinto|mejor)\b", texto) else anterior.get("atributos", {})
                    session["marco_dialogo"] = {"macro": clave, "atributos": atributos_previos, "pregunta": anterior.get('pregunta'), "candidatos": list(clasificador.INTENCIONES_MACRO[clave]["opciones"])}
                    session["campos_pendientes"] = list(campos or anterior.get("campos", []))
                    resuelta = _resolver_macro(clave, mensaje, session["campos_pendientes"], confianza)
                    if resuelta:
                        return resuelta
                    return _preguntar_macro(clave, confianza, _grupo_para_menu(clave, texto))

        # El dataset heredado asocia algunas consultas de servicios básicos a
        # T_008, cuyo nombre vigente corresponde a prescripción/rectificación.
        # Pedir aclaración evita presentar ese procedimiento como equivalente.
        if intent == "T_008" and confianza >= UMBRAL_DUDA_MIN and re.search(r"\b(?:luz|agua|desague|electrica|electrificacion|servicios basicos)\b", texto) and not re.search(r"\b(?:prescripcion|rectificacion|linderos|supletorio)\b", texto):
            _limpiar_pendientes()
            session["aclaracion_tramites"] = "planos_servicios"
            session["campos_pendientes"] = list(campos)
            pregunta = "¿Lo necesitas para conseguir agua o luz en un terreno que ocupas, o para una prescripción o rectificación de áreas y linderos?"
            session["ultima_pregunta"] = pregunta
            return _respuesta("clarification", pregunta, intent="aclarar_visacion_servicios", confianza=round(confianza, 4), opciones=[])

        # Un agradecimiento es una pausa, no el fin de la conversación.
        if texto in _AGRADECIMIENTOS and confianza >= UMBRAL_DUDA_MIN:
            return _respuesta("charla_casual", "¡De nada! Puedes seguir preguntándome sobre este trámite o consultar otro de la MDJLO.", intent="agradecimiento", confianza=round(confianza, 4))
        if not macro and intent == "despedida" and confianza >= UMBRAL_DUDA_MIN and not campos and not es_correccion_de_contexto(texto):
            _limpiar_pendientes()
            session.pop("tramite_actual", None)
            session.pop("macro_resuelta", None)
            session.pop("alternativa_revisor", None)
            for clave in ('consultas_en_espera', 'consulta_multiple_pendiente', 'recordatorio_consulta'):
                session.pop(clave, None)
            return _respuesta("despedida", random.choice(MENSAJES_DESPEDIDA), intent=intent, confianza=round(confianza, 4))
        if not macro and intent == "saludo" and confianza >= UMBRAL_DUDA_MIN and not campos:
            return _respuesta("saludo", random.choice(MENSAJES_SALUDO), intent=intent, confianza=round(confianza, 4))
        if not macro and intent == "charla_casual" and confianza >= UMBRAL_DUDA_MIN and not campos:
            if re.search(r"\b(?:llamas|nombre|quien eres)\b", texto):
                respuesta = "Soy Leonardito, el asistente virtual de la Municipalidad Distrital de José Leonardo Ortiz. Te oriento sobre requisitos, costos y plazos del TUPA municipal."
            else:
                respuesta = "Aquí estoy para ayudarte con los trámites de la Municipalidad de José Leonardo Ortiz. Cuéntame qué necesitas realizar."
            return _respuesta("charla_casual", respuesta, intent=intent, confianza=round(confianza, 4))

        if macro:
            config_macro = clasificador.INTENCIONES_MACRO[macro]
            es_control_menu = texto in config_macro["opciones"] or texto in config_macro["frases_no_seguro"]
            grupo_detectado = clasificador.resolver_grupo_macro(macro, texto)
            atributos_contextuales = extraer_atributos(texto, macro, session.get("marco_dialogo", {}).get("pregunta"))
            if intent == "fuera_de_dominio" and confianza >= UMBRAL_CONFIANZA and not es_control_menu and not grupo_detectado and not detalle_contextual and not rectificacion:
                return _respuesta("fallback", "Sobre ese tema no tengo información. Si quieres, seguimos con tu consulta municipal.", intent=intent, confianza=round(confianza, 4))
            if intent == "fuera_de_dominio" and confianza >= UMBRAL_CONFIANZA and not es_control_menu and not grupo_detectado and not detalle_contextual and not rectificacion and not es_detalle_del_caso(texto, macro):
                return _respuesta("fallback", "Sobre ese tema no tengo información. Podemos seguir con tu trámite cuando quieras.", intent=intent, confianza=round(confianza, 4))
            # Una consulta reconocida sobre otro tema abandona el menú anterior.
            nuevo_tema = bool(tema and tema != macro) or (confianza >= UMBRAL_CONFIANZA and intent != macro and not respuesta_slot and (intent in clasificador.INTENCIONES_MACRO or str(intent).startswith("T_")))
            if not nuevo_tema:
                if campos:
                    session['campos_pendientes']=list(campos)
                resuelta = _resolver_macro(macro, mensaje, campos or session.get("campos_pendientes", ()), confianza)
                if resuelta:
                    return resuelta
                if texto in {"volver", "atras", "ver grupos", "otro grupo"}:
                    return _preguntar_macro(macro, confianza)
                grupo = _grupo_para_menu(macro, texto, session.get("macro_grupo_pendiente"))
                return _preguntar_macro(macro, confianza, grupo=grupo)
            _limpiar_pendientes()

        pendiente = session.get("tramite_pendiente")
        if pendiente:
            confirmacion = confirmacion_natural(texto)
            if confirmacion == "si":
                tramite = Tramite.query.filter_by(id_tramite=pendiente).first()
                if tramite:
                    return _responder_tramite(tramite, session.get("campos_pendientes", ()), intent="confirmacion_positiva")
            if confirmacion == "no" and len(texto.split()) <= 5:
                _limpiar_pendientes()
                return _respuesta("clarification_rejected", "Entendido. Cuéntame con más detalle qué trámite municipal necesitas.", intent="confirmacion_negativa")
            _limpiar_pendientes()

        if campos and _seguimiento_natural(texto):
            actual = Tramite.query.filter_by(id_tramite=session.get("tramite_actual")).first() if session.get("tramite_actual") else None
            if actual:
                return _responder_tramite(actual, campos, intent="consultar_" + "_y_".join(campos), confianza=confianza)
            session.pop("tramite_actual", None)
            session["campos_pendientes"] = list(campos)
            return _respuesta("fallback", "Con gusto te indico esa información. ¿De qué trámite de la Municipalidad de José Leonardo Ortiz se trata?", intent="sin_contexto", confianza=round(confianza, 4))

        if texto in {"donde lo hago", "donde se hace", "donde lo tramito", "se puede por internet", "es presencial o virtual", "cual es la modalidad", "cual es el horario", "cual es la direccion"}:
            return _respuesta("derivacion", "El catálogo disponible registra requisitos, costos y plazos. No tengo registrada la modalidad, la dirección de atención ni el horario de este trámite. Confirma esos datos con la Municipalidad de José Leonardo Ortiz antes de acudir o enviar documentos.", intent="informacion_no_disponible")

        if session.get("tramite_actual") and es_correccion_de_contexto(texto) and confianza < UMBRAL_CONFIANZA:
            _limpiar_pendientes()
            session.pop("tramite_actual", None)
            return _respuesta("correction", "Entendido. ¿Sobre qué trámite necesitas información entonces?", intent="correccion_contexto")

        campos = campos or tuple(session.get("campos_pendientes", ()))
        if UMBRAL_DUDA_MIN <= confianza < UMBRAL_DUDA_MAX and str(intent).startswith("T_"):
            tramite = Tramite.query.filter_by(id_tramite=intent).first()
            if tramite:
                return _confirmar_tramite(tramite, campos, confianza)
        # Un tema general reconocido en zona de duda se puede aclarar, sin dar datos.
        config_macro = clasificador.INTENCIONES_MACRO.get(intent, {})
        resolucion_lexica = (any(clasificador.contiene_frase_exacta(texto, ancla) for ancla in config_macro.get("anclas", ()))
                             and len(clasificador.coincidencias_intencion_macro(intent, texto)) == 1)
        if config_macro and (resolucion_lexica or confianza >= UMBRAL_DUDA_MIN):
            session["campos_pendientes"] = list(campos)
            resuelta = _resolver_macro(intent, mensaje, campos, confianza)
            if resuelta:
                return resuelta
            grupo = _grupo_para_menu(intent, texto)
            return _preguntar_macro(intent, confianza, grupo=grupo)
        if intent == "fuera_de_dominio" or confianza < UMBRAL_CONFIANZA:
            return _fallback(intent, confianza, mensaje, campos)
        tramite = Tramite.query.filter_by(id_tramite=intent).first()
        if tramite:
            return _responder_tramite(tramite, campos, confianza=confianza)
        return _fallback(intent, confianza, mensaje, campos)
    except Exception:
        logger.exception("Error al procesar la consulta municipal")
        return jsonify(status="error", mensaje="Ocurrió un error al procesar tu consulta. Intenta nuevamente más tarde."), 500
