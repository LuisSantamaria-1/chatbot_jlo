"""Consultas sobre asuntos distintos: conserva campos separados y permite elegir."""
import re

from backend.chatbot.entendimiento import tema_explicito, extraer_atributos, normalizar_dialogo, PERFILES
from backend.chatbot.politica import solicitud_completa


def etiqueta(macro):
    return {'consultar_puesto_mercado':'el puesto del mercado',
            'consultar_matrimonio_civil':'el matrimonio civil',
            'consultar_licencia_funcionamiento':'la licencia del negocio'}.get(macro,macro.removeprefix('consultar_').replace('_',' '))


def separar(texto):
    partes=re.split(r'\s+(?:y\s+)?(?:tambien|ademas)\s+|\s+y\s+(?=cuanto|que requisitos|que papeles|quiero|necesito)',texto)
    if len(partes)!=2:
        return []
    consultas=[{'texto':p,'macro':tema_explicito(p)} for p in partes]
    if all(c['macro'] for c in consultas) and consultas[0]['macro']!=consultas[1]['macro']:
        return consultas
    return []


def preparar(mensaje, sesion):
    """Devuelve mensaje a procesar o una pregunta para elegir, sin mezclar campos."""
    t=normalizar_dialogo(mensaje)
    dobles=separar(t)
    if dobles:
        sesion['consultas_en_espera']=dobles
        sesion['consulta_multiple_pendiente']=True
        sesion.pop('recordatorio_consulta',None)
        return None, 'Son dos consultas: '+etiqueta(dobles[0]['macro'])+' y '+etiqueta(dobles[1]['macro'])+'. ¿Con cuál comenzamos?'
    pendientes=list(sesion.get('consultas_en_espera',()))
    if not pendientes:
        return mensaje,None
    indices=[]
    if re.search(r'\b(?:continuar con la otra|sigamos|la otra consulta|la segunda|segundo|continuemos)\b',t):
        indices=[1 if len(pendientes)>1 else 0]
    elif re.search(r'\b(?:la primera|primero)\b',t):
        indices=[0]
    else:
        tema=tema_explicito(t)
        indices=[i for i,c in enumerate(pendientes) if tema==c['macro']]
        if not indices and len(t.split())<=7:
            relevantes=[]
            for i,c in enumerate(pendientes):
                palabras=set(etiqueta(c['macro']).split())-{'el','la','del','de','civil','licencia'}
                pregunta='lugar' if c['macro']=='consultar_matrimonio_civil' else None
                atributos=extraer_atributos(t,c['macro'],pregunta)
                perfiles=PERFILES.get(c['macro'],{}).values()
                evidencia=any(v==p.get(k) for k,v in atributos.items() for p in perfiles)
                if set(t.split()) & palabras or (sesion.get('consulta_multiple_pendiente') and not tema and evidencia):
                    relevantes.append(i)
            indices=relevantes
    if len(indices)==1:
        elegido=pendientes.pop(indices[0])
        sesion['consultas_en_espera']=pendientes
        sesion.pop('consulta_multiple_pendiente',None)
        sesion.pop('recordatorio_consulta',None)
        detalle=t
        if elegido['macro']=='consultar_matrimonio_civil' and t in {'muni','municipalidad','municipal','municipio'}:
            detalle='en la municipalidad'
        return elegido['texto']+' '+detalle,None
    if sesion.get('consulta_multiple_pendiente'):
        if solicitud_completa(t) and tema_explicito(t) not in {c['macro'] for c in pendientes}:
            sesion.pop('consultas_en_espera',None)
            sesion.pop('consulta_multiple_pendiente',None)
            return mensaje,None
        return None,'¿Empezamos por '+etiqueta(pendientes[0]['macro'])+' o por '+etiqueta(pendientes[1]['macro'])+'? Puedes decirlo con tus palabras.'
    return mensaje,None
