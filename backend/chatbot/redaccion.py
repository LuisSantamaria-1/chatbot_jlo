"""Presentación ciudadana; conserva los datos oficiales que devuelve la API."""
import re

from backend.nlp.preprocesamiento import preprocesar_texto


def requisito_legible(texto):
    texto = re.sub(r'\b(?:DDJJ|DJ)\b', 'declaración jurada', texto, flags=re.I)
    formatos = {
        'FUT': 'Formulario Único de Trámite',
        'FUE': 'Formulario Único de Edificación',
        'FUHU': 'Formulario Único de Habilitaciones Urbanas',
    }
    for sigla, significado in formatos.items():
        if preprocesar_texto(significado) not in preprocesar_texto(texto):
            texto = re.sub(r'\b' + sigla + r'\b', f'{sigla} ({significado})', texto)
    return texto


def respuesta_solicitada(tramite, campos, requisitos):
    """Solo muestra los campos pedidos; el valor original sigue en el JSON."""
    partes = []
    nombre = tramite.nombre
    for campo in campos:
        if campo == 'requisitos':
            encabezado = f'Para el trámite «{nombre}», necesitas:'
            if requisitos:
                lista = '\n'.join(f'{i}. {requisito_legible(r)}' if len(requisitos) > 5 else f'- {requisito_legible(r)}'
                                  for i, r in enumerate(requisitos, 1))
                partes.append(encabezado + '\n\n' + lista)
            else:
                partes.append(f'Los requisitos para «{nombre}» no están registrados. Consúltalos en la municipalidad.')
        elif campo == 'costo':
            valor = (tramite.costo or '').strip()
            if not valor or valor.lower() == 'no especificado':
                partes.append(f'El costo para «{nombre}» no está registrado. Confírmalo en la municipalidad.')
            elif valor.lower() == 'gratuito':
                partes.append(f'El trámite «{nombre}» es gratuito.')
            else:
                partes.append(f'El costo para «{nombre}» es {valor.rstrip(".")}.')
        elif campo == 'plazo':
            valor = (tramite.plazo or '').strip()
            if not valor or valor.lower() == 'no especificado':
                partes.append(f'El plazo para «{nombre}» no está registrado. Confírmalo en la municipalidad.')
            elif re.match(r'^0(?:\s|$)', valor) or 'aprobacion automatica' in preprocesar_texto(valor):
                partes.append(f'El plazo para «{nombre}» es: Inmediato ({valor}).')
            else:
                partes.append(f'El plazo para «{nombre}» es de {valor.rstrip(".")}.')
    return partes


def pide_explicacion(texto):
    # «Riesgo alto, creo que es» contiene «que es», pero sigue siendo una
    # descripción del local. Una explicación debe ser el propósito de la frase.
    return bool(re.search(r'^(?:(?:y|hola|oye|disculpa|no se|no entiendo)\s+)*(?:que es|que significa|que quiere decir|a que te refieres|explicame|me explicas|para que sirve|que diferencia hay)\b', texto)
                or re.search(r'\b(?:eso|esto) que (?:es|significa)\b', texto))


def explicar_concepto(texto, pregunta=None):
    if 'reconsideracion' in texto and 'apelacion' in texto:
        return ('En el catálogo, la reconsideración exige que presentes una nueva prueba para volver a revisar una decisión. '
                'La apelación es otro recurso: su ficha pide un escrito fundamentado y la resolución municipal que impugnas. '
                'Para orientar el trámite, necesito saber si tienes una prueba nueva; no puedo decidir por ti qué recurso corresponde a tu caso.')
    if re.search(r'\b(?:itse|defensa civil)\b', texto):
        return ('ITSE significa Inspección Técnica de Seguridad en Edificaciones. Es la inspección de seguridad del establecimiento. '
                'En el catálogo hay trámites para obtener el certificado, renovarlo y pedir un duplicado. '
                'El riesgo debe ser el que figure en la evaluación; no se determina solo porque el negocio sea una pollería o sea grande.')
    if 'parametros' in texto or 'urbanisticos' in texto:
        return ('El Certificado de Parámetros Urbanísticos y Edificatorios está relacionado con las condiciones urbanísticas y de edificación de un predio. '
                'Puedo indicarte los requisitos, el costo y el plazo registrados en su ficha; no determinar los parámetros particulares de tu terreno.')
    if re.search(r'\b(?:declaratoria de fabrica|declaratoria de edificacion)\b', texto):
        return ('La declaratoria de edificación, también llamada declaratoria de fábrica, describe una edificación construida. '
                'En este catálogo aparece junto con la conformidad de obra, con alternativas según la modalidad y si hubo cambios respecto a los planos. '
                'Para orientarte necesito esos datos; no basta con saber que la obra está terminada.')
    if 'divorcio ulterior' in texto:
        return 'El divorcio ulterior es el trámite que viene después de la separación de mutuo acuerdo. La ficha del catálogo pide el documento que aprobó esa separación.'
    if 'separacion' in texto or pregunta == 'separacion':
        return ('La separación de mutuo acuerdo es la primera etapa que estamos consultando. '
                'Necesito saber si ya tienes el documento que aprueba esa separación o si recién vas a solicitarla.')
    if pregunta == 'raza':
        return 'Te pregunto la raza de tu perro para distinguir el registro común del registro de perros considerados potencialmente peligrosos.'
    if pregunta == 'riesgo':
        return 'Me refiero a la categoría que figura en la evaluación de seguridad de tu local. Si todavía no tienes esa evaluación, dímelo; puedo mostrarte los requisitos comunes.'
    return None


def referencia_concepto(texto):
    """Identidad del concepto explicado, sin afirmar que ya se eligió un trámite."""
    if re.search(r'\b(?:itse|defensa civil)\b', texto):
        return {'macro': 'consultar_itse'}
    if 'parametros' in texto or 'urbanisticos' in texto:
        return {'id_tramite': 'T_033'}
    if re.search(r'\b(?:declaratoria de fabrica|declaratoria de edificacion)\b', texto):
        return {'macro': 'consultar_conformidad_obra'}
    if 'reconsideracion' in texto and 'apelacion' in texto:
        return {'macro': 'consultar_recurso_administrativo'}
    return None


def objetivo_especifico(texto, contexto=None):
    """Operación + objeto distingue un trámite específico de su familia general."""
    cambiar_fecha = re.search(r'\b(?:postergar|postergacion|aplazar|reprogramar|cambiar la fecha|cambiar de fecha)\b', texto)
    matrimonio = re.search(r'\b(?:boda|matrimonio|casamiento)\b', texto) or (contexto == 'consultar_matrimonio_civil' and re.search(r'\bceremonia\b', texto))
    if cambiar_fecha and matrimonio:
        return 'T_248'
    return None


def matrimonio_ya_celebrado(texto):
    return bool(re.search(r'\b(?:me case|nos casamos|ya estoy casad[oa])\b', texto) and
                re.search(r'\b(?:otro distrito|distrito diferente|soy de otro|mi distrito|este distrito)\b', texto))
