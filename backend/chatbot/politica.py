"""Decisiones de conversación comunes a todas las intenciones del catálogo."""

import hashlib
import re


FUERA_DOMINIO = ('Mi información se limita al catálogo de trámites de la MDJLO. Sobre ese tema no tengo datos registrados. '
                 'Si necesitas requisitos, costos o plazos de un trámite del catálogo, cuéntame cuál.')
PRESENTACION = ('Soy Leonardito, un asistente virtual 🤖. Te digo qué requisitos pide la municipalidad, '
                'cuánto cuesta y cuánto demora cada trámite. Por ejemplo: abrir un negocio, construir, '
                'casarte, registrar a tu mascota, tu mototaxi o tu puesto en el mercado. ¿Qué quieres hacer?')
CATEGORIAS = {
    '1': ('Abrir o manejar un negocio', r'negocio|funcionamiento|tienda|empresa|comercio'),
    '2': ('Construir o mejorar mi casa o terreno', r'casa|vivienda|terreno|construccion|construir|obra'),
    '3': ('Un certificado o documento', r'certificado|documento|constancia|papel'),
    '4': ('Matrimonio o divorcio', r'matrimonio|divorcio|casarme|familia|gestion familiar'),
    '5': ('Mi mascota', r'mascota|perro|canino'),
    '6': ('Mototaxi o transporte', r'mototaxi|transporte|vehiculo'),
    '7': ('Un puesto en el mercado', r'puesto|mercado'),
    '8': ('Otra cosa', r'otra cosa|otro tema'),
}


def huella(texto):
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()[:16]


def solicitud_completa(texto):
    """Una nueva petición con su propio objeto no hereda los datos del caso previo."""
    accion = re.search(r'\b(?:quiero|queremos|quisiera|necesito|deseo|voy a|vamos a|tengo que|me gustaria|ya termine|se me perdio|me robaron|como (?:hago|saco|solicito|renuevo))\b', texto)
    if re.search(r'\b(?:quiero que sea|necesito que sea|quiero hacerlo|lo quiero|necesito que lo)\b', texto):
        return False
    objeto = re.search(r'\b(?:casa|vivienda|departamentos|edificio|terreno|lote|negocio|local|licencia|certificado|puesto|mercado|matrimonio|casarme|divorcio|divorciarme|perro|mascota|mototaxi|vehiculo|antena|obra|proyecto|bodega|restaurante|discoteca|peluqueria|botica|gimnasio)\b', texto)
    operacion = re.search(r'\b(?:reclamar|impugnar|apelar|postergar|construir|edificar|demoler|registrar|inscribir|habilitar|instalar|casarme|divorciarme)\b', texto)
    return bool(accion and (objeto or operacion or len(texto.split()) >= 7))


def fuera_de_ambito(texto):
    if re.search(r'\b(?:donde (?:queda|esta|se ubica).*(?:muni|municipalidad)|hasta (?:que|a que) hora atienden|hora de atencion)\b', texto):
        return 'No tengo registradas la dirección ni las horas de atención en el catálogo que consulto. Confírmalas directamente con la Municipalidad de José Leonardo Ortiz. Puedo seguir orientándote sobre requisitos, costos y plazos del TUPA.'
    if re.search(r'\b(?:arbitrios|denunci\w*.*(?:vecino|construccion)|vecino.*denunci\w*)\b',texto):
        return 'Esa consulta se relaciona con la municipalidad, pero no tengo esa gestión registrada en el catálogo que manejo. Confirma el canal de atención directamente con la MDJLO; no puedo indicarte aquí un costo o procedimiento que no tengo documentado.'
    if re.search(r'\b(?:quiero jugar|estudiar.*examen|que hora es)\b', texto):
        return FUERA_DOMINIO
    if re.search(r'\b(?:bache|hueco en (?:mi |la )?(?:calle|pista)|reparacion de pista)\b', texto):
        return 'Un bache o reparación de pista no es un trámite del TUPA, así que no puedo orientarte aquí. Te recomiendo comunicarte con la municipalidad.'
    if re.search(r'\b(?:horario de atencion|a que hora (?:abren|atienden|cierran)|cuando (?:abren|atienden))\b', texto):
        return 'No tengo el horario de atención a la mano. Consúltalo directamente en la municipalidad. Si quieres, te oriento con algún trámite.'
    if re.search(r'\b(?:pasaje|pension 65|sacar mi dni|saco mi dni|renovar mi dni|bitcoin|pizza|receta de|juega peru|sueldo del alcalde)\b', texto) or re.search(r'\b(?:pago|pagar|cancelar)\b.*\brecibo de (?:luz|agua)\b', texto):
        return FUERA_DOMINIO
    return None


def licencia_ambigua(texto):
    return bool(re.fullmatch(r'(?:(?:quiero|necesito|no se|saber|que|cual|una|la|mi|sacar|solicitar|tramitar|ps|oe)\s+)*licencia(?:\s+(?:necesito|sacar|solicitar))?', texto))


def menu_categorias():
    return ('¿Lo necesitas para un negocio, una casa o terreno, o un documento? '
            'También puedo orientarte sobre familia, mascotas, mercados o transporte. '
            'Cuéntame qué quieres conseguir.')


def elegir_categoria(texto):
    if texto in CATEGORIAS:
        return texto
    coincidencias = [k for k, (_, patron) in CATEGORIAS.items() if re.search(r'\b(?:' + patron + r')\b', texto)]
    return coincidencias[0] if len(coincidencias) == 1 else None


def detalle_catalogo(texto):
    """Preguntas elípticas sobre una condición; nunca una petición de otro trámite."""
    return (not solicitud_completa(texto) and bool(re.search(
        r'\b(?:si (?:ya |yo )?tengo|y si|que pasa si|mas de|menos de|ya no puedo|puedo hacerlo|eso significa|a que se refiere|que significa esa|que quiere decir|es obligatorio|es necesario)\b', texto)))
