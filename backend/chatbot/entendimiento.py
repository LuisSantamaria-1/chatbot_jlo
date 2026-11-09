"""Comprensión por turnos: acumula atributos y pregunta solo lo que falta.

No modifica el preprocesamiento ni el clasificador entrenado. Los candidatos
son siempre procedimientos existentes de una macro municipal conocida.
"""

import re
from functools import lru_cache

from backend.nlp import clasificador as nlp
from backend.nlp.preprocesamiento import preprocesar_texto, interpretar_confirmacion
from backend.chatbot.semantica import sugerir
from backend.chatbot.recuperacion import proponer


@lru_cache(maxsize=1)
def _vocabulario_dialogo():
    fuentes = [frase for c in nlp.INTENCIONES_MACRO.values() for d in c['opciones'].values()
               for frase in [d['etiqueta'], *d.get('frases', ()), *d.get('palabras', ()),
                             *d.get('excluir', ()), *(' '.join(g) for g in d.get('todas', ()))]]
    return set(preprocesar_texto(' '.join(fuentes)).split())


@lru_cache(maxsize=2048)
def _errata_larga(palabra):
    """Una sola errata y un único término largo conocido. Nunca palabras cortas."""
    vocabulario = _vocabulario_dialogo()
    if len(palabra) < 7 or palabra in vocabulario:
        return palabra
    candidatos = []
    for termino in vocabulario:
        if len(termino) < 8 or abs(len(termino) - len(palabra)) > 1:
            continue
        if len(termino) == len(palabra):
            diferencias = [i for i, (a, b) in enumerate(zip(termino, palabra)) if a != b]
            coincide = len(diferencias) == 1 or (len(diferencias) == 2 and
                diferencias[1] == diferencias[0] + 1 and
                termino[diferencias[0]:diferencias[1]+1] == palabra[diferencias[0]:diferencias[1]+1][::-1])
        else:
            largo, corto = sorted((termino, palabra), key=len, reverse=True)
            coincide = any(largo[:i] + largo[i+1:] == corto for i in range(len(largo)))
        if coincide:
            candidatos.append(termino)
    return candidatos[0] if len(candidatos) == 1 else palabra


def normalizar_dialogo(texto):
    texto = re.sub(r'([a-záéíóúñ])\1{2,}', r'\1', str(texto), flags=re.I)
    texto = re.sub(r'(\d+)[,.](\d{1,2})(?!\d)', r'\1 decimal \2', str(texto))
    texto = preprocesar_texto(texto)
    equivalencias = {
        r'\b(?:mi jato|mi hogar)\b': 'mi casa',
        r'\b(?:municipio|comuna)\b': 'municipalidad',
        r'\b(?:gobierno|sector publico)\b': 'estado',
        r'\b(?:pequenito|chiquitito|pequenito|pequenita)\b': 'pequeno',
        r'\b(?:grandazo|grandote)\b': 'grande',
        r'\b(?:se extravio|se perdio|no encuentro)\b': 'perdi',
        r'\b(?:fotocopia|reponer|reposicion)\b': 'duplicado',
        r'\b(?:salon|salon de eventos|local alquilado)\b': 'local publico',
        r'\botro sitio\b': 'otro lugar',
        r'\bhu\b': 'habilitacion urbana',
        r'\bcasita\b': 'casa',
        r'\bperrito\b': 'perro',
        r'\bncesito\b': 'necesito',
        r'\btamos\b': 'estamos',
        r'\bno{2,}\b': 'no',
        r'\b(?:remodelando|remodelamos|remodelo|remodelemos)\b': 'remodelar',
        r'\b(?:ampliando|ampliamos|amplio|ampliemos)\b': 'ampliar',
        r'\b(?:construyendo|construimos|construyo|construiremos)\b': 'construir',
        r'\b(?:habilitando|habilitamos|habilito)\b': 'habilitar',
        r'\b(?:renovando|renovamos|renuevo)\b': 'renovar',
        r'\b(?:registrando|registramos|registro a|inscribiendo|inscribimos)\b': 'registrar',
        r'\b(?:juntando|juntamos|uniendo|unimos)\b': 'juntar',
        r'\b(?:dividiendo|dividimos)\b': 'dividir',
        r'\b(?:cambiando|cambiamos)\b': 'cambiar',
        r'\b(?:instalando|instalamos)\b': 'instalar',
        r'\b(?:casarnos|casarse|casar)\b': 'casarme',
        r'\b(?:divorciar|divorciarnos|divorciarse)\b': 'divorciarme',
        r'\b(?:renuevan|renueven|renuevas)\b': 'renovar',
        r'\b(?:restaurant|restauran)\b': 'restaurante',
        r'\b(?:pelgoroso|peligoroso)\b': 'peligroso',
        r'\blicenci\b': 'licencia',
        r'\burjent[e]*\b': 'urgente',
        r'\b(?:tbm|tambn)\b': 'tambien',
        r'\bvoi\b': 'voy',
        r'\b(?:rajada|rajado)\b': 'con rajaduras',
        r'\bse va caer\b': 'en riesgo de colapso',
    }
    for patron, valor in equivalencias.items():
        texto = re.sub(patron, valor, texto)
    texto = ' '.join(_errata_larga(p) for p in texto.split())
    return re.sub(r'\s+', ' ', re.sub(r'\b(?:pe|pues|tmr|ptmr|ptm|oe|ps)\b', '', texto)).strip()


def _perfiles():
    perfiles = {}

    def agregar(macro, campo, valores):
        opciones = perfiles.setdefault('consultar_' + macro, {})
        claves = list(nlp.INTENCIONES_MACRO['consultar_' + macro]['opciones'])
        for clave, valor in zip(claves, valores):
            if valor is not None:
                opciones.setdefault(clave, {})[campo] = valor

    agregar('matrimonio_civil', 'lugar', ['municipal', 'publico', 'municipal', 'publico', 'domicilio', 'alcalde', 'comunitaria'])
    agregar('matrimonio_civil', 'jurisdiccion', [None, 'dentro', None, 'fuera', 'dentro', None, None])
    agregar('matrimonio_civil', 'horario', ['habitual', None, 'especial', None, None, None, None])
    agregar('conexion_agua', 'persona', ['natural', 'juridica'])
    agregar('publicidad_exterior', 'iluminacion', ['sin', 'con'])
    agregar('certificacion_sanitaria', 'gestion', ['obtener', 'duplicado', 'cese'])
    agregar('registro_canino', 'raza', ['comun', 'peligrosa'])
    agregar('evento_publico', 'evento', ['espectaculo', 'feria'])
    agregar('tramite_vehicular', 'gestion', ['empadronar', 'renovar', 'duplicado', 'baja', 'datos'])
    agregar('gestion_flota_vehicular', 'gestion', ['obtener', 'renovar', 'incrementar', 'paradero'])
    agregar('divorcio', 'separacion', ['inicial', 'aprobada'])
    agregar('puesto_mercado', 'gestion', ['obtener', 'renovar', 'heredar', 'vacante', 'remodelar', 'giro'])
    agregar('numeracion_municipal', 'gestion', ['certificar', 'asignar'])
    agregar('catastro_predial', 'gestion', ['positivo', 'negativo', 'datos'])
    agregar('recurso_administrativo', 'pruebas', ['nuevas', 'sin_nuevas'])
    agregar('habilitacion_urbana', 'categoria', ['publica', 'bono', 'residencial', 'modificar', 'venta_lotes', 'venta_casas', 'protegida', 'reurbanizar', 'aislado', 'colindante', 'industrial'])
    agregar('habilitacion_urbana', 'modalidad', list('aabbccccddd'))
    agregar('lotes_urbanos', 'gestion', ['dividir', 'juntar'])
    for macro in ('licencia_funcionamiento', 'licencia_cesionario'):
        riesgos = ['bajo', 'medio', 'alto', 'muy_alto', 'corporativa'] if macro.endswith('funcionamiento') else ['medio', 'alto', 'muy_alto']
        agregar(macro, 'riesgo', riesgos)
    agregar('itse', 'gestion', ['obtener'] * 4 + ['renovar'] * 4 + ['duplicado'])
    agregar('itse', 'riesgo', ['bajo', 'medio', 'alto', 'muy_alto'] * 2 + [None])
    agregar('licencia_construccion', 'categoria', ['unifamiliar', 'pequena', 'grande', 'mixto', 'patrimonio'])
    agregar('licencia_ampliacion_remodelacion', 'categoria', ['ampliar_pequena', 'sin_estructura', 'menor', 'estructura', 'comercial', 'especial'])
    agregar('licencia_ampliacion_remodelacion', 'operacion', ['ampliar', 'remodelar', ['ampliar', 'remodelar'], ['ampliar', 'remodelar'], ['ampliar', 'remodelar'], ['ampliar', 'remodelar']])
    agregar('licencia_ampliacion_remodelacion', 'inmueble', ['vivienda'] * 4 + ['edificio', 'especial'])
    agregar('licencia_demolicion', 'alcance', ['total', 'total', 'total', 'parcial'])
    agregar('licencia_demolicion', 'categoria', ['pequena', 'mediana', 'grande', 'parcial'])
    agregar('licencia_cerco', 'propiedad', ['propia', 'comun'])
    agregar('licencia_edificacion_no_vivienda', 'uso', ['comercio', 'comercio', 'mercado', 'mercado', 'deporte', 'deporte', 'industria', 'especial', 'oficinas', 'otro'])
    agregar('licencia_edificacion_no_vivienda', 'tamano', ['pequeno', 'grande'] * 3 + [None] * 4)
    agregar('licencia_edificacion_estado', 'uso', ['vivienda', 'infraestructura', 'defensa', 'universidad', 'salud', 'educacion'])
    agregar('modificacion_proyecto_edificacion', 'fase', ['antes'] * 3 + ['despues'] * 8)
    agregar('modificacion_proyecto_edificacion', 'magnitud', [None] * 3 + ['menor'] * 4 + ['mayor'] * 4)
    agregar('modificacion_proyecto_edificacion', 'modalidad', list('bcdabcdabcd'))
    agregar('anteproyecto_consulta', 'modalidad', list('bcd'))
    agregar('conformidad_obra', 'cambios', ['sin', 'sin'] + ['con'] * 4 + [None])
    agregar('conformidad_obra', 'modalidad', ['a', ['b', 'c', 'd']] + list('abcd') + [None])
    agregar('conformidad_obra', 'gestion', ['conformidad'] * 6 + ['declaracion'])
    agregar('conformidad_obra_anticipada', 'cambios', ['sin'] * 3 + ['con'] * 3)
    agregar('conformidad_obra_anticipada', 'modalidad', list('bcdbcd'))
    for macro in ('proyecto_integral_edificacion', 'proyecto_integral_habilitacion'):
        agregar(macro, 'fase_proyecto', ['solo', 'solo', 'simultaneo', 'simultaneo', 'aprobado', 'modificar'])
        agregar(macro, 'modalidad', ['c', 'd', 'c', 'd', None, 'b'])
    agregar('prorroga_revalidacion_licencia', 'tipo_licencia', ['edificacion', 'edificacion', 'habilitacion', 'habilitacion'])
    agregar('prorroga_revalidacion_licencia', 'vigencia', ['vigente', 'vencida', 'vigente', 'vencida'])
    agregar('modificacion_habilitacion_urbana', 'modalidad', list('abcd'))
    agregar('independizacion_terreno_rustico', 'fase', ['solo', 'solo'] + ['habilitar'] * 4)
    agregar('independizacion_terreno_rustico', 'ubicacion', ['urbana', 'expansion', None, None, None, 'aislado'])
    agregar('independizacion_terreno_rustico', 'modalidad', [None, None, 'b', 'c', 'd', 'd'])
    agregar('recepcion_obras_habilitacion', 'cambios', ['sin'] * 4 + ['con'] * 4 + [None])
    agregar('recepcion_obras_habilitacion', 'modalidad', list('abcdabcd') + [None])
    agregar('recepcion_obras_habilitacion', 'alcance', ['total'] * 8 + ['parcial'])
    agregar('regularizacion_obras', 'tipo_obra', ['habilitacion', 'ambas', 'edificacion'])
    agregar('libre_disponibilidad', 'propiedad', ['privada', 'publica'])
    agregar('obras_via_publica', 'gestion', ['vereda', 'conformidad', 'materiales', 'redes', 'apertura'])
    agregar('telecomunicaciones', 'gestion', ['conformidad', 'banda', 'antena', 'infraestructura', 'ampliar_plazo'])
    agregar('gestion_licencia', 'gestion', ['giro', 'transferir', 'cese', 'duplicado'])
    return perfiles


PERFILES = _perfiles()


def confirmacion_natural(texto):
    t = normalizar_dialogo(texto)
    if re.fullmatch(r'(?:(?:si|claro|correcto|exacto) )?(?:eso|ese|esa)(?: es)?(?: quiero| necesito| busco| mismo| estoy buscando)?', t):
        return 'si'
    return interpretar_confirmacion(t)


def campos_admitidos(macro):
    campos = {campo for perfil in PERFILES.get(macro, {}).values() for campo in perfil}
    if macro in {'consultar_licencia_construccion', 'consultar_licencia_demolicion', 'consultar_licencia_edificacion_no_vivienda'}:
        campos.update({'pisos', 'area', 'unica', 'area_comparador', 'pisos_comparador'})
    if macro == 'consultar_licencia_ampliacion_remodelacion':
        campos.update({'area', 'supera_limite'})
    return campos


def extraer_atributos(texto, macro, pregunta=None):
    t = normalizar_dialogo(texto)
    datos = {}

    def tiene(patron):
        return bool(re.search(patron, t))

    afirmacion = t in {'si', 'sip', 'claro', 'correcto', 'asi es', 'exacto', 'ya', 'si ya', 'si lo tengo'} or tiene(r'\bsi (?:ya )?(?:lo|la) tengo\b')
    negacion = t in {'no', 'nop', 'todavia no', 'aun no', 'no todavia'} or tiene(r'\bno (?:lo|la) tengo\b')
    if afirmacion or negacion:
        booleanos = {
            'iluminacion': ('con', 'sin'), 'cambios': ('con', 'sin'),
            'separacion': ('aprobada', 'inicial'), 'vigencia': ('vigente', 'vencida'),
            'alcance': ('total', 'parcial'), 'pruebas': ('nuevas', 'sin_nuevas'),
            'codigo': ('positivo', 'negativo'),
            'unica': (True, False),
        }
        if pregunta in booleanos:
            campo = 'gestion' if pregunta == 'codigo' else pregunta
            datos[campo] = booleanos[pregunta][0 if afirmacion else 1]
        if pregunta == 'fase':
            datos['fase'] = ('habilitar' if afirmacion else 'solo') if macro == 'consultar_independizacion_terreno_rustico' else ('despues' if afirmacion else 'antes')

    if tiene(r'\b(?:modalidad|modal|tipo)\s+([abcd])\b'):
        datos['modalidad'] = re.search(r'\b(?:modalidad|modal|tipo)\s+([abcd])\b', t)[1]
    elif pregunta == 'modalidad' and tiene(r'^(?:(?:creo que|es|tengo)\s+)?(?:la\s+)?[abcd]$'):
        datos['modalidad'] = t.split()[-1]
    if tiene(r'\bmuy alto\b'):
        datos['riesgo'] = 'muy_alto'
    elif tiene(r'\balto\b'):
        datos['riesgo'] = 'alto'
    elif tiene(r'\b(?:medio|moderado|mediano)\b'):
        datos['riesgo'] = 'medio'
    elif tiene(r'\b(?:bajo|baja)\b') and not tiene(r'dar de baja'):
        datos['riesgo'] = 'bajo'
    if tiene(r'\b(?:corporativa|mercado completo|galeria completa|centro comercial completo)\b'):
        datos['riesgo'] = 'corporativa'
    if tiene(r'\b(?:sin cambios|sin modificaciones|sin variaciones|igual|igualito|tal cual|no cambie|no cambie nada)\b'):
        datos['cambios'] = 'sin'
    elif tiene(r'\b(?:con cambios|con modificaciones|con variaciones|distinto|diferente|cambie|modifique)\b'):
        datos['cambios'] = 'con'
    if tiene(r'\b(?:pequeno|menor|no sustancial|poquito|poquita cosa)\b'):
        datos['magnitud'] = 'menor'
    elif tiene(r'\b(?:grande|sustancial|importante|mucho)\b'):
        datos['magnitud'] = 'mayor'
    if tiene(r'\b(?:aun no|todavia no|antes de|sin licencia emitida|estoy esperando)\b'):
        datos['fase'] = 'antes'
    elif tiene(r'\b(?:ya tengo|ya me dieron|ya salio|despues de|ya esta emitida)\b'):
        datos['fase'] = 'despues'
    if tiene(r'\b(?:perdi|perdida|duplicado|me robaron|extravie|otra copia)\b'):
        datos['gestion'] = 'duplicado'
    elif tiene(r'\b(?:renovar|renovarlo|renovarla|renuevo|renovacion|vencido|vencida|vencio)\b'):
        datos['gestion'] = 'renovar'
    elif tiene(r'\b(?:dar de baja|cerrar|cerre mi negocio|ya cerre|cierro|cierre|cese|ya no voy a atender)\b'):
        datos['gestion'] = 'cese' if macro in {'consultar_gestion_licencia', 'consultar_certificacion_sanitaria'} else 'baja'
    elif tiene(r'\b(?:por primera vez|primero|primera|nuevo|nueva|inicial|obtener|sacar por primera)\b'):
        datos['gestion'] = 'obtener'
    if 'gestion' not in datos and 'obtener' in {p.get('gestion') for p in PERFILES.get(macro, {}).values()} and tiene(r'\b(?:sacar|pedir|solicitar|obtener|que necesito|que piden)\b'):
        datos['gestion'] = 'obtener'
    if macro == 'consultar_matrimonio_civil':
        if tiene(r'\b(?:comunitari[oa]|colectiv[oa]|con otras parejas|varias parejas|grupal)\b'):
            datos['lugar'] = 'comunitaria'
        elif tiene(r'\b(?:alcalde|burgomaestre)\b'):
            datos['lugar'] = 'alcalde'
        elif tiene(r'\b(?:mi casa|en casa|domicilio|la casa|mi vivienda)\b'):
            datos['lugar'] = 'domicilio'
        elif tiene(r'\b(?:fuera (?:de la |del |de )?(?:municipalidad|muni|local)|otro (?:lugar|local)|otra (?:parte|ubicacion))\b'):
            datos['lugar'] = ['publico', 'domicilio']
        elif tiene(r'\b(?:local publico|local particular|colegio|local de eventos)\b'):
            datos['lugar'] = 'publico'
        elif tiene(r'\b(?:en la muni|en la municipalidad|dentro de la muni|dentro de la municipalidad|local municipal|la municipalidad|la muni)\b'):
            datos['lugar'] = 'municipal'
        elif pregunta == 'lugar' and t in {'muni', 'municipalidad', 'municipal', 'municipio'}:
            datos['lugar'] = 'municipal'
        if tiene(r'\b(?:fuera del distrito|fuera de jlo|otro distrito|otra ciudad|chiclayo|pimentel)\b'):
            datos['jurisdiccion'] = 'fuera'
            if 'lugar' not in datos:
                datos['lugar'] = 'publico'
        elif tiene(r'\b(?:dentro del distrito|dentro de jlo|en jlo|aqui en el distrito|aca en el distrito|mismo distrito)\b'):
            datos['jurisdiccion'] = 'dentro'
        elif pregunta == 'jurisdiccion' and t in {'dentro', 'aqui', 'aca', 'aca nomas', 'en el distrito', 'en jose leonardo ortiz'}:
            datos['jurisdiccion'] = 'dentro'
        elif pregunta == 'jurisdiccion' and t in {'fuera', 'afuera', 'en otro'}:
            datos['jurisdiccion'] = 'fuera'
        if pregunta == 'lugar' and t in {'publico', 'uno alquilado', 'en uno alquilado', 'en un local', 'un local', 'el local'}:
            datos['lugar'] = 'publico'
        if tiene(r'\b(?:noche|nocturno|sabado|domingo|fuera de horario|fuera del horario|feriado|fin de semana)\b'):
            datos['horario'] = 'especial'
        elif tiene(r'\b(?:normal|habitual|horario de trabajo|de dia|en la manana|dia de semana)\b'):
            datos['horario'] = 'habitual'
        if datos.get('lugar') == 'municipal' and 'horario' not in datos:
            datos['horario'] = 'habitual'
        if datos.get('lugar') == 'municipal' and 'jurisdiccion' not in datos:
            datos['jurisdiccion'] = 'dentro'
    if macro == 'consultar_conexion_agua':
        if tiene(r'\b(?:empresa|negocio|juridica|constructora|razon social)\b'):
            datos['persona'] = 'juridica'
        elif tiene(r'\b(?:mi casa|vivienda|particular|mi nombre|natural|mio|para mi)\b'):
            datos['persona'] = 'natural'
    if macro == 'consultar_publicidad_exterior':
        if tiene(r'\b(?:sin luz|sin luces|sin iluminacion|no es (?:luminoso|iluminado)|no brilla|no (?:tiene|lleva|llevara|tendra)(?: ninguna| ningun)? (?:luz|luces|iluminacion)|simple|pintado|sin led)\b'):
            datos['iluminacion'] = 'sin'
        elif tiene(r'\b(?:luces|luz|led|neon|luminoso|iluminado|brilla)\b'):
            datos['iluminacion'] = 'con'
    if macro == 'consultar_divorcio':
        if tiene(r'\b(?:no tengo|no lo tengo|no la tengo|primero|primera|aun no|todavia no|empezar|comenzar|mutuo acuerdo)\b'):
            datos['separacion'] = 'inicial'
        elif tiene(r'\b(?:ya tengo|aprobada|ya pasaron|dos meses|ulterior|final)\b'):
            datos['separacion'] = 'aprobada'
        elif tiene(r'\bsi (?:ya )?lo tengo\b'):
            datos['separacion'] = 'aprobada'
    if macro == 'consultar_registro_canino':
        if tiene(r'\b(?:mestizo|criollo|comun|no es peligroso|no peligrosa)\b'):
            datos['raza'] = 'comun'
        elif tiene(r'\b(?:pitbull|rottweiler|bull terrier|peligrosa|peligroso|dogo)\b'):
            datos['raza'] = 'peligrosa'
    if macro == 'consultar_evento_publico':
        if tiene(r'\b(?:circo|feria|juegos mecanicos)\b'):
            datos['evento'] = 'feria'
        elif tiene(r'\b(?:concierto|espectaculo|show|festival|evento musical)\b'):
            datos['evento'] = 'espectaculo'
    acciones = {
        'giro': r'\b(?:giro|rubro|vender otra cosa|cambiar lo que vendo)\b',
        'transferir': r'\b(?:transferir|traspasar|otro dueno|nuevo propietario|comprador|denominacion|pasar (?:mi|la) licencia|a nombre de otra persona)\b',
        'heredar': r'\b(?:fallecio|murio|fallecid[oa]|heredar|herencia)\b',
        'vacante': r'\b(?:abandonado|vacante|vacio|sin ocupar|desocupado)\b',
        'remodelar': r'\b(?:arreglar|remodelar|reparar|techo|mantenimiento)\b',
        'empadronar': r'\b(?:empadronar|empadronarme|registrar|inscribir|formalizar)\b',
        'incrementar': r'\b(?:aumentar|agregar|incrementar|mas unidades|mas vehiculos)\b',
        'paradero': r'\b(?:paradero|parada|espera)\b',
        'datos': r'\b(?:datos|nombre del propietario|nombre del titular|razon social|corregir)\b',
        'dividir': r'\b(?:dividir|partir|separar|fraccionar|subdividir|sublotes)\b',
        'juntar': r'\b(?:juntar|unir|fusionar|acumular|uno solo)\b',
    }
    disponibles = {p.get('gestion') for p in PERFILES.get(macro, {}).values()}
    for valor, patron in acciones.items():
        if valor in disponibles and tiene(patron):
            datos['gestion'] = valor
    if macro == 'consultar_puesto_mercado' and datos.get('gestion') == 'empadronar':
        datos['gestion'] = 'obtener'
    if macro == 'consultar_certificacion_sanitaria' and datos.get('gestion') == 'renovar':
        datos['gestion'] = 'obtener'
    if macro == 'consultar_numeracion_municipal':
        if tiene(r'\b(?:asignar|asignen|nuevo numero|proyecto aprobado|departamento)\b'):
            datos['gestion'] = 'asignar'
        elif tiene(r'\b(?:ya existe|ya tiene|ya esta construida|certificar|certificado|numero de mi casa)\b'):
            datos['gestion'] = 'certificar'
    if macro == 'consultar_catastro_predial':
        if tiene(r'\b(?:no tiene|no figura|sin codigo|no esta registrado|negativo)\b'):
            datos['gestion'] = 'negativo'
        elif tiene(r'\b(?:ya tiene|si tiene|ya esta registrado|positivo)\b'):
            datos['gestion'] = 'positivo'
    if macro == 'consultar_recurso_administrativo':
        if tiene(r'\b(?:no tengo pruebas|sin pruebas|sin prueba|interpretaron mal|cuestion de ley|apelar)\b'):
            datos['pruebas'] = 'sin_nuevas'
        elif tiene(r'\b(?:nueva prueba|nuevo documento|prueba nueva|pruebas nuevas|reconsideracion)\b'):
            datos['pruebas'] = 'nuevas'
    if macro in {'consultar_licencia_demolicion', 'consultar_recepcion_obras_habilitacion'}:
        if tiene(r'\b(?:solo una parte|una parte|parcial|solo una etapa)\b'):
            datos['alcance'] = 'parcial'
        elif tiene(r'\b(?:toda|todo|completa|total)\b'):
            datos['alcance'] = 'total'
    if macro == 'consultar_licencia_cerco':
        if tiene(r'\b(?:condominio|comun|compartid[oa]|junta de propietarios)\b'):
            datos['propiedad'] = 'comun'
        elif tiene(r'\b(?:propio|propia|mi lote|mi terreno|es mio)\b'):
            datos['propiedad'] = 'propia'
    if macro in {'consultar_licencia_construccion', 'consultar_licencia_demolicion', 'consultar_licencia_edificacion_no_vivienda'}:
        numeros = {'uno': 1, 'un': 1, 'una': 1, 'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5, 'seis': 6, 'siete': 7, 'ocho': 8, 'nueve': 9, 'diez': 10}
        texto_numerico = re.sub(r'\b(' + '|'.join(numeros) + r')\b', lambda m: str(numeros[m[0]]), t)
        texto_numerico = re.sub(r'(\d+) decimal (\d+)', r'\1.\2', texto_numerico)
        medida = re.search(r'\b(\d+(?:\.\d+)?)\s*pisos?\b', texto_numerico)
        if medida:
            datos['pisos'] = int(float(medida[1]))
            if re.search(r'\bmas de\s*$', texto_numerico[:medida.start()]):
                datos['pisos_comparador'] = 'mayor'
            else:
                datos['pisos_comparador'] = 'exacto'
        elif pregunta == 'pisos' and re.fullmatch(r'(?:(?:serian|son|tiene|de) )?\d+', texto_numerico):
            datos['pisos'] = int(texto_numerico.split()[-1])
            datos['pisos_comparador'] = 'exacto'
        area = re.search(r'\b(\d+(?:\s+\d{3})?(?:\.\d+)?)\s*(?:m2|metros cuadrados|metros|personas|asistentes)\b', texto_numerico)
        if area:
            datos['area'] = float(area[1].replace(' ', ''))
            if re.search(r'\bmas de\s*$', texto_numerico[:area.start()]):
                datos['area_comparador'] = 'mayor'
            else:
                datos['area_comparador'] = 'exacto'
        elif pregunta in {'area', 'tamano'} and re.fullmatch(r'\d+(?:\s+\d{3})?(?:\.\d+)?', texto_numerico):
            datos['area'] = float(texto_numerico.replace(' ', ''))
            datos['area_comparador'] = 'exacto'
        if macro == 'consultar_licencia_construccion' and tiene(r'\b(?:departamentos|multifamiliar|condominio)\b'):
            datos['unica'] = False
        elif macro == 'consultar_licencia_construccion' and tiene(r'\b(?:unica (?:construccion|edificacion)|unica vivienda del lote)\b'):
            datos['unica'] = True
        elif macro == 'consultar_licencia_construccion' and pregunta == 'unica' and tiene(r'\b(?:una sola|solo una|unica|una nomas)\b'):
            datos['unica'] = True
    if macro == 'consultar_licencia_ampliacion_remodelacion':
        if tiene(r'\b(?:remodelar|remodelacion|por dentro|refaccionar)\b'):
            datos['operacion'] = 'remodelar'
        elif tiene(r'\b(?:ampliar|agrandar|ampliacion|poner un .*piso|(?:segundo|tercer|cuarto|otro|nuevo) piso)\b'):
            datos['operacion'] = 'ampliar'
        medida = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:m2|metros cuadrados|metros)\b', t)
        if medida:
            datos['area'] = float(medida[1])
            datos['supera_limite'] = datos['area'] > 200 or (datos['area'] == 200 and tiene(r'\bmas de\b'))
        if tiene(r'\b(?:multifamiliar|comercial|oficinas|centro comercial)\b'):
            datos['categoria'] = 'comercial'
            datos['inmueble'] = 'edificio'
        elif tiene(r'\b(?:fabrica|industria|mercado|colegio|clinica|hotel|terminal|hospital|estadio)\b'):
            datos['categoria'] = 'especial'
            datos['inmueble'] = 'especial'
        elif tiene(r'\b(?:casa|vivienda|hogar)\b'):
            datos['inmueble'] = 'vivienda'
        elif tiene(r'\bedificio\b'):
            datos['inmueble'] = 'edificio'
    if macro == 'consultar_licencia_edificacion_no_vivienda':
        usos = {'mercado': 'mercado', 'estadio': 'deporte', 'coliseo': 'deporte', 'deportivo': 'deporte',
                'comercial': 'comercio', 'cine': 'comercio', 'teatro': 'comercio', 'galeria': 'comercio',
                'fabrica': 'industria', 'industrial': 'industria', 'colegio': 'especial', 'clinica': 'especial',
                'hotel': 'especial', 'terminal': 'especial', 'oficinas': 'oficinas', 'banco': 'oficinas'}
        for palabra, uso in usos.items():
            if tiene(r'\b' + palabra + r'\b'):
                datos['uso'] = uso
    if macro in {'consultar_conformidad_obra', 'consultar_obras_via_publica', 'consultar_telecomunicaciones'}:
        if tiene(r'\b(?:ya termine|ya conclui|conformidad|terminada|finalizada)\b'):
            datos['gestion'] = 'conformidad'
        if macro == 'consultar_conformidad_obra' and tiene(r'declaracion municipal'):
            datos['gestion'] = 'declaracion'
    if macro.startswith('consultar_proyecto_integral'):
        if tiene(r'\b(?:modificar|cambiar|modificacion)\b'):
            datos['fase_proyecto'] = 'modificar'
        elif tiene(r'\b(?:ya tengo|ya esta aprobado|ya aprobaron|ya aprobado|aprobado anteriormente)\b'):
            datos['fase_proyecto'] = 'aprobado'
        elif tiene(r'\b(?:al mismo tiempo|a la vez|simultaneo|junto con la licencia|proyecto y licencia)\b'):
            datos['fase_proyecto'] = 'simultaneo'
        elif tiene(r'\b(?:solo|solamente|unicamente|sin licencia)\b'):
            datos['fase_proyecto'] = 'solo'
    if macro == 'consultar_prorroga_revalidacion_licencia':
        if tiene(r'habilitacion'):
            datos['tipo_licencia'] = 'habilitacion'
        elif tiene(r'edificacion|construccion|\b(?:casa|vivienda|edificio)\b'):
            datos['tipo_licencia'] = 'edificacion'
        if tiene(r'vencida|vencio|revalidar|ya vencio'):
            datos['vigencia'] = 'vencida'
        elif tiene(r'vigente|todavia vale|aun vale|prorrogar|prorroga'):
            datos['vigencia'] = 'vigente'
    if macro == 'consultar_regularizacion_obras':
        if tiene(r'\b(?:casa|edificacion|construccion|construi|construida)\b') and not tiene(r'\b(?:habilitacion|habilite|lotes y calles|terreno|terrenos)\b'):
            datos['tipo_obra'] = 'edificacion'
    if macro == 'consultar_independizacion_terreno_rustico':
        if tiene(r'\b(?:solo dividir|solo independizar|solo parcelar|sin habilitar)\b'):
            datos['fase'] = 'solo'
        elif tiene(r'\b(?:dividir y habilitar|habilitar tambien|tambien habilitar)\b'):
            datos['fase'] = 'habilitar'
        if tiene(r'\b(?:no colinda|no colindante|sin colindancia|aislado)\b'):
            datos['ubicacion'] = 'aislado'
        elif tiene(r'\b(?:expansion urbana|urbanizable inmediata)\b'):
            datos['ubicacion'] = 'expansion'
        elif tiene(r'\b(?:dentro de la ciudad|zona urbana)\b'):
            datos['ubicacion'] = 'urbana'
    if macro == 'consultar_obras_via_publica' and tiene(r'\b(?:arena|ladrillos|materiales)\b') and tiene(r'\b(?:dejar|depositar|ocupar|vereda|berma)\b'):
        datos['gestion'] = 'materiales'
    if macro == 'consultar_gestion_flota_vehicular' and tiene(r'\b(?:formar|crear|constituir|nueva)\b') and tiene(r'\b(?:empresa|asociacion)\b'):
        datos['gestion'] = 'obtener'
    # Una alternativa reconocida aporta sus atributos en cualquier macro. Esto
    # permite rectificar un caso resuelto sin conservar su categoría anterior.
    coincidencias = nlp.coincidencias_intencion_macro(macro, t)
    if len(coincidencias) == 1 and macro not in {
        'consultar_licencia_construccion', 'consultar_licencia_demolicion',
        'consultar_licencia_edificacion_no_vivienda',
    }:
        perfil = PERFILES.get(macro, {}).get(coincidencias[0], {})
        datos = {**perfil, **datos}
    elif len(coincidencias) == 1 and macro == 'consultar_licencia_edificacion_no_vivienda':
        # El uso se puede identificar sin inferir un área ni una capacidad.
        datos.setdefault('uso', PERFILES[macro][coincidencias[0]]['uso'])
    return {campo: valor for campo, valor in datos.items() if campo in campos_admitidos(macro)}


def _coincide(valor, esperado):
    actuales = set(valor if isinstance(valor, list) else [valor])
    posibles = set(esperado if isinstance(esperado, list) else [esperado])
    return bool(actuales & posibles)


def filtrar(macro, atributos, iniciales=None):
    perfiles = PERFILES.get(macro, {})
    candidatos = list(iniciales or nlp.INTENCIONES_MACRO[macro]['opciones'])
    for campo, valor in atributos.items():
        if campo == 'horario' and atributos.get('lugar') != 'municipal':
            continue
        # Un atributo que no aplica a una opción no la descarta. Por ejemplo,
        # la jurisdicción distingue ceremonias externas, no el local municipal.
        # El resultado debe ser igual aunque Flask reordene las claves en sesión.
        candidatos = [k for k in candidatos if campo not in perfiles.get(k, {})
                      or _coincide(valor, perfiles[k][campo])]
    return candidatos


def es_alternativa(texto):
    return bool(re.search(r'\b(?:otr[oa]s? (?:forma|manera|opcion|modalidad|alternativa)|mas (?:formas|opciones)|de otra forma|algo diferente)\b', texto))


PREGUNTAS = {
    'lugar': '¿Dónde te gustaría celebrar el matrimonio: en la municipalidad, en otro local o en tu domicilio?',
    'jurisdiccion': '¿Sería dentro de José Leonardo Ortiz o en otro distrito?',
    'horario': '¿En horario habitual de atención o fuera de ese horario, por ejemplo un fin de semana?',
    'persona': '¿La conexión será a tu nombre como persona particular o a nombre de una empresa?',
    'iluminacion': '¿El anuncio va a llevar alguna luz?',
    'raza': '¿Es un perro mestizo o común, o una raza considerada potencialmente peligrosa?',
    'evento': '¿Organizas un espectáculo con público o vas a instalar una feria, un circo o juegos mecánicos?',
    'separacion': '¿Ya tienes la separación de mutuo acuerdo aprobada? Me refiero al documento que confirma esa primera etapa.',
    'riesgo': '¿Qué nivel de riesgo te indicó la municipalidad para tu local: bajo, medio, alto o muy alto?',
    'pruebas': '¿Tienes alguna prueba nueva para presentar contra la decisión?',
    'modalidad': '¿Qué modalidad figura en tu licencia o proyecto: A, B, C o D?',
    'cambios': '¿Cambiaste algo respecto a los planos aprobados?',
    'magnitud': '¿Es un cambio menor del proyecto o una modificación importante?',
    'fase': '¿Ya te entregaron la licencia?',
    'fase_proyecto': '¿Quieres aprobar solo el proyecto, pedir también la licencia de una etapa, o ya tienes el proyecto aprobado?',
    'alcance': '¿El trámite es por toda la obra?',
    'vigencia': '¿Tu licencia todavía está vigente?',
    'tipo_licencia': '¿La licencia es de construcción de una edificación o de habilitación urbana de un terreno?',
    'propiedad': '¿El terreno o cerco es propio, compartido o corresponde a un área pública?',
    'ubicacion': '¿El terreno está en zona urbana, en expansión urbana o no colinda con la ciudad?',
    'tipo_obra': '¿Quieres regularizar solo la habilitación del terreno, solo una construcción o ambas cosas?',
    'tamano': '¿Qué área o capacidad tendrá el proyecto?',
    'operacion': '¿Vas a ampliar el área construida o remodelar lo que ya existe?',
}


def siguiente_pregunta(macro, marco):
    candidatos = marco.get('candidatos') or list(nlp.INTENCIONES_MACRO[macro]['opciones'])
    atributos = marco.get('atributos', {})
    if macro == 'consultar_habilitacion_urbana' and len(candidatos) > 5:
        return 'caso', '¿Qué quieres hacer con el terreno: un proyecto del Estado, uno residencial, habilitar y construir a la vez, u otro caso?'
    if macro == 'consultar_habilitacion_urbana' and set(candidatos) == {'c','d'}:
        return 'caso', '¿Vas a habilitar un terreno residencial nuevo o a modificar una etapa de un proyecto que ya fue aprobado?'
    if macro == 'consultar_itse' and 'gestion' not in atributos:
        return 'gestion', '¿Es tu primera inspección de seguridad, vas a renovar el certificado o necesitas una copia porque lo perdiste?'
    if macro == 'consultar_catastro_predial' and 'gestion' not in atributos:
        return 'codigo', 'Para el certificado, ¿tu predio ya tiene código catastral? Si buscas corregir sus datos, también puedo ayudarte con eso.'
    if macro == 'consultar_independizacion_terreno_rustico' and 'fase' not in atributos:
        return 'fase', '¿También quieres habilitar el terreno, además de dividirlo?'
    if macro == 'consultar_licencia_construccion':
        if not atributos.get('pisos'):
            return 'pisos', '¿De cuántos pisos será la vivienda?'
        if not atributos.get('area'):
            if atributos.get('unica') is False and atributos.get('pisos', 99) <= 5:
                return 'area', 'Para departamentos de hasta cinco pisos revisaríamos la modalidad B si el área no supera 3000 m². ¿Cuántos metros cuadrados tendrá el área techada total?'
            return 'area', '¿Cuántos metros cuadrados tendrá en total el área techada?'
        if atributos['area'] <= 120 and 'unica' not in atributos:
            return 'unica', '¿Será una sola vivienda y la única construcción de ese lote?'
    if macro == 'consultar_licencia_demolicion' and atributos.get('alcance') == 'total' and not atributos.get('pisos'):
        return 'pisos', '¿Cuántos pisos tiene la construcción que vas a demoler?'
    if macro == 'consultar_licencia_edificacion_no_vivienda' and atributos.get('uso') in {'comercio', 'mercado', 'deporte'} and 'area' not in atributos:
        if atributos['uso'] == 'deporte':
            return 'area', '¿Para cuántas personas estará previsto el local deportivo?'
        return 'area', '¿Cuántos metros cuadrados tendrá el local?'
    if macro == 'consultar_matrimonio_civil':
        lugares = {v for k in candidatos for v in ([PERFILES[macro][k].get('lugar')] if not isinstance(PERFILES[macro][k].get('lugar'), list) else PERFILES[macro][k]['lugar'])}
        if lugares <= {'publico', 'domicilio'}:
            if 'jurisdiccion' not in atributos and any('jurisdiccion' in PERFILES[macro][k] for k in candidatos):
                return 'jurisdiccion', PREGUNTAS['jurisdiccion']
            return 'lugar', 'Bien, dentro de JLO. ¿La ceremonia sería en un local público, como un salón, o en tu domicilio?'
        if lugares == {'municipal'}:
            return 'horario', PREGUNTAS['horario']
        return 'lugar', PREGUNTAS['lugar']
    if macro in {'consultar_licencia_funcionamiento', 'consultar_licencia_cesionario', 'consultar_itse'} and 'riesgo' not in atributos:
        return 'riesgo', '¿La municipalidad ya evaluó tu local? Para darte el costo correcto necesito la categoría que figura en esa evaluación: bajo, medio, alto o muy alto. Si aún no la tienes, dímelo y vemos los requisitos comunes.'
    if macro == 'consultar_licencia_ampliacion_remodelacion' and 'operacion' not in atributos:
        return 'operacion', PREGUNTAS['operacion']
    if macro == 'consultar_licencia_ampliacion_remodelacion' and 'inmueble' not in atributos:
        return 'inmueble', '¿Los trabajos son en una vivienda, en un edificio de departamentos o comercial, o en un local como colegio, hotel o fábrica?'
    prioridad = ['gestion', 'fase', 'fase_proyecto', 'alcance', 'persona', 'iluminacion', 'raza', 'evento', 'separacion', 'pruebas', 'tipo_licencia', 'vigencia', 'tipo_obra', 'categoria', 'uso', 'magnitud', 'cambios', 'riesgo', 'modalidad', 'ubicacion', 'propiedad', 'tamano']
    for campo in prioridad:
        valores = {str(PERFILES.get(macro, {}).get(k, {}).get(campo)) for k in candidatos}
        if len(valores) > 1 and campo not in atributos and campo in PREGUNTAS:
            return campo, PREGUNTAS[campo]
    grupos = nlp.INTENCIONES_MACRO[macro].get('grupos', {})
    if len(candidatos) > 5 and grupos:
        etiquetas = [g['etiqueta'].lower() for g in grupos.values() if set(g['opciones']) & set(candidatos)]
    else:
        etiquetas = list(dict.fromkeys(nlp.INTENCIONES_MACRO[macro]['opciones'][k]['etiqueta'].lower() for k in candidatos))
    if len(etiquetas) == 2:
        return 'caso', f'¿Buscas {etiquetas[0]} o {etiquetas[1]}?'
    if len(etiquetas) == 1:
        marco['propuesta'] = candidatos[0]
        return 'confirmacion', f'¿Te refieres a {etiquetas[0]}?'
    alternativas = ', '.join(etiquetas[:-1]) + ' o ' + etiquetas[-1]
    return 'caso', f'¿Tu consulta es sobre {alternativas}? Cuéntame cuál se parece a tu caso.'


def comprender(macro, texto, marco=None):
    """Combina evidencias parciales, conserva ambigüedad y admite rectificaciones."""
    config = nlp.INTENCIONES_MACRO[macro]
    marco = dict(marco or {})
    if marco.get('macro') != macro:
        marco = {'macro': macro, 'atributos': {}, 'candidatos': list(config['opciones'])}
    t = normalizar_dialogo(texto)
    # Una frase con información nueva invalida la propuesta anterior, sea cual
    # sea la macro. Las confirmaciones breves se atienden antes, en el diálogo.
    marco.pop('propuesta', None)
    if marco.get('pregunta') == 'riesgo' and t in {'no', 'no la tengo', 'no me evaluaron', 'aun no', 'todavia no'}:
        return 'no_seguro', marco
    if es_alternativa(t) and not extraer_atributos(t, macro, marco.get('pregunta')):
        marco = {'macro': macro, 'atributos': {}, 'candidatos': list(config['opciones']), 'alternativas': True}
        return None, marco
    opcion, codigo = nlp.resolver_intencion_macro(macro, t, estricto=True)
    if opcion == 'no_seguro':
        return 'no_seguro', marco
    seleccion = nlp.interpretar_seleccion_macro(macro, t)
    if marco.get('pregunta') == 'modalidad' and re.fullmatch(r'[abcd]', t):
        # «B» responde la modalidad preguntada; «opción b» sí elige la fila b.
        seleccion = None
        opcion = None
    coincidencias = nlp.coincidencias_intencion_macro(macro, t)
    if not seleccion and len(coincidencias) > 1 and re.search(r'\b(?:o|u)\b', t):
        marco.update(candidatos=list(coincidencias), atributos={})
        return None, marco
    if re.search(r'\bno (?:quiero|deseo|necesito|busco|prefiero)\b', t) and not re.search(r'\b(?:pero|sino|mejor)\b', t) and coincidencias:
        rechazadas = set(marco.get('rechazadas', ())) | set(coincidencias)
        marco = {'macro': macro, 'atributos': {}, 'candidatos': [k for k in config['opciones'] if k not in rechazadas],
                 'rechazadas': sorted(rechazadas)}
        return None, marco
    if opcion:
        marco['rechazadas'] = [k for k in marco.get('rechazadas', ()) if k != opcion]
    atributos = {k:v for k,v in marco.get('atributos', {}).items() if k in campos_admitidos(macro)}
    nuevos = extraer_atributos(t, macro, marco.get('pregunta'))
    atributos.update(nuevos)
    if opcion and macro in {'consultar_licencia_construccion', 'consultar_licencia_demolicion'}:
        # La categoría guardada de una respuesta anterior no sustituye las
        # medidas del nuevo caso que el ciudadano está corrigiendo.
        atributos.pop('categoria', None)
    if macro == 'consultar_licencia_ampliacion_remodelacion' and atributos.get('supera_limite'):
        marco['rechazadas'] = list(set(marco.get('rechazadas', ())) | {'a'})
    if macro == 'consultar_licencia_edificacion_no_vivienda':
        umbral = {'comercio': 30000, 'mercado': 15000, 'deporte': 20000}.get(atributos.get('uso'))
        if umbral and 'area' in atributos:
            mayor = atributos.get('area_comparador') == 'mayor'
            if mayor and atributos['area'] < umbral:
                atributos.pop('tamano', None)
                opcion = None
            else:
                atributos['tamano'] = 'grande' if atributos['area'] > umbral or (mayor and atributos['area'] == umbral) else 'pequeno'
        elif umbral and not seleccion:
            opcion = None
    if macro == 'consultar_licencia_construccion' and not seleccion:
        pisos, area = atributos.get('pisos'), atributos.get('area')
        if (pisos and (pisos > 5 or pisos == 5 and atributos.get('pisos_comparador') == 'mayor')) or (area and (area > 3000 or area == 3000 and atributos.get('area_comparador') == 'mayor')):
            atributos['categoria'] = 'grande'
        elif pisos and area:
            if area <= 120 and atributos.get('unica') is True:
                atributos['categoria'] = 'unifamiliar'
            elif area > 120 or atributos.get('unica') is False:
                atributos['categoria'] = 'pequena'
            else:
                opcion = None
        elif opcion not in {'d', 'e'}:
            opcion = None
    if macro == 'consultar_licencia_demolicion' and atributos.get('pisos'):
        minimo = atributos['pisos'] + (1 if atributos.get('pisos_comparador') == 'mayor' else 0)
        atributos['categoria'] = 'grande' if minimo > 5 else ('mediana' if minimo > 3 else 'pequena')
        if opcion == 'c' and re.search(r'\b(?:explosivos|dinamita|implosion)\b', t):
            atributos['categoria'] = 'grande'
        elif opcion == 'b' and re.search(r'\b(?:sotano|semisotano)\b', t) and minimo <= 5:
            atributos['categoria'] = 'mediana'
        elif opcion == 'd':
            atributos['categoria'] = 'parcial'
    # El horario municipal no restringe una ceremonia en otro lugar.
    if macro == 'consultar_matrimonio_civil' and atributos.get('lugar') != 'municipal':
        atributos.pop('horario', None)
    grupo = nlp.resolver_grupo_macro(macro, t)
    restringidos = config.get('grupos', {}).get(grupo, {}).get('opciones')
    if opcion and restringidos and opcion not in restringidos:
        # La opción específica prevalece sobre una frase amplia que también
        # nombra un grupo (p. ej. dividir y habilitar SIN colindancia).
        restringidos = None
        grupo = None
        marco.pop('restriccion', None)
        marco.pop('grupo', None)
    if restringidos:
        marco['grupo'] = grupo
        marco['restriccion'] = list(restringidos)
        # Cambiar de grupo reemplaza los atributos que solo pertenecían al
        # grupo anterior. Conserva los datos compatibles, como la modalidad.
        atributos = {campo: valor for campo, valor in atributos.items()
                     if filtrar(macro, {campo: valor}, restringidos)}
    if nuevos and marco.get('restriccion') and not filtrar(macro, atributos, marco['restriccion']):
        marco.pop('restriccion', None)
        marco.pop('grupo', None)
    candidatos = filtrar(macro, atributos, marco.get('restriccion'))
    if not candidatos and nuevos:
        # Una rectificación explícita reemplaza los detalles incompatibles.
        # No conservar «inversión pública / A» si el vecino aclara «modalidad B».
        atributos = dict(nuevos)
        marco.pop('restriccion', None)
        marco.pop('grupo', None)
        candidatos = filtrar(macro, atributos)
    candidatos = [k for k in candidatos if k not in marco.get('rechazadas', ())]
    if seleccion:
        elegido = seleccion
    elif opcion and (not nuevos or opcion in candidatos):
        elegido = opcion
    elif len(candidatos) == 1 and (nuevos or grupo):
        elegido = candidatos[0]
    else:
        elegido = None
    if not candidatos:
        # Una contradicción no termina en un trámite al azar: pedir el detalle otra vez.
        candidatos = list(config['opciones'])
        atributos = nuevos
    marco.update(atributos=atributos, candidatos=candidatos)
    if elegido:
        return elegido, marco
    neutras = set('quiero queremos necesito necesitamos deseo saber conocer sacar solicitar tramitar gestionar hacer obtener como que para de del la el los las un una mi mis en a es pe pues por favor me se lo si y'.split())
    neutras.update(macro.removeprefix('consultar_').split('_'))
    for ancla in config.get('anclas', ()):
        neutras.update(normalizar_dialogo(ancla).split())
    hay_detalle = bool(set(t.split()) - neutras)
    campos_criticos = {'riesgo', 'raza', 'modalidad', 'lugar'}
    falta_dato_critico = any(campo not in atributos and len({str(PERFILES.get(macro, {}).get(k, {}).get(campo)) for k in candidatos}) > 1
                             for campo in campos_criticos)
    limites = {
        'consultar_licencia_construccion': {'pisos', 'area'},
        'consultar_licencia_ampliacion_remodelacion': {'operacion', 'area'},
        'consultar_licencia_demolicion': {'alcance', 'pisos'},
    }
    falta_dato_critico = falta_dato_critico or bool(limites.get(macro, set()) - atributos.keys())
    if not nuevos and not grupo and hay_detalle and not falta_dato_critico and not re.fullmatch(r'[1-5]', t):
        elegible = {k: config['opciones'][k] for k in candidatos}
        contexto = macro.removeprefix('consultar_').replace('_', ' ')
        propuesta = proponer(macro, t, elegible) or sugerir(macro, t, elegible, contexto)
        if propuesta:
            marco['propuesta'] = propuesta
    return None, marco


def acto_conversacional(texto):
    t = normalizar_dialogo(texto)
    if re.fullmatch(r'(?:ninguno(?: de (?:ellos|esos))?|(?:ya )?no quiero nada|jaj+a+j+a*|jaja+)(?: jaj+a+j+a*)?', t):
        return 'sin_interes'
    if t in {'no entendi', 'no entiendo', 'eso no es lo que pregunte', 'no es lo que pregunte', 'eso no te pregunte'}:
        return 'reiniciar'
    if re.fullmatch(r'(?:ah |ah ya |ya |bueno |listo |ok )?(?:muchas |muchisimas )?gracias(?: pe| por la ayuda)?', t):
        return 'agradecimiento'
    if t in {'ok', 'okay', 'oka', 'ya', 'listo', 'dale', 'vale', 'entiendo', 'entendido', 'esta bien', 'bueno', 'si', 'sip', 'claro', 'aja'}:
        return 'acuse'
    if t in {'no', 'nop', 'nope', 'nel', 'ninguno', 'ninguno jajaja', 'todavia no', 'ahora no'}:
        return 'negacion'
    if t in {'que', 'como', 'no entendi', 'no entiendo', 'a que te refieres', 'explicame', 'me explicas', 'no comprendo'}:
        return 'explicacion'
    if re.fullmatch(r'(?:hola|ola|holi|buenas|buenos dias|buenas tardes|buenas noches|que tal)(?: pe| amigo| leonardito)?', t):
        return 'saludo'
    if re.fullmatch(r'(?:hola+|holi|buenas)(?: como estas| buenas| buenos dias| buenas tardes| buenas noches| quisiera hacer una consulta)?', t):
        return 'saludo'
    if t in {'como estas', 'como te va', 'como andas', 'todo bien', 'que haces'}:
        return 'bienestar'
    if re.search(r'\b(?:quiero hablar contigo|quiero conversar|podemos conversar|puedo hablar contigo|quiero charlar)\b', t):
        return 'conversar'
    if t in {'adios', 'chau', 'chao', 'bye', 'hasta luego', 'hasta pronto', 'nos vemos', 'me voy', 'no gracias adios'}:
        return 'despedida'
    if t in {'quien eres', 'como te llamas', 'cual es tu nombre', 'que puedes hacer', 'eres un robot', 'en que me ayudas'}:
        return 'presentacion'
    return None


def es_continuacion(texto, macro):
    t = normalizar_dialogo(texto)
    if es_alternativa(t) or extraer_atributos(t, macro):
        return True
    return bool(re.search(r'^(?:y |pero |entonces |en ese caso |mejor |y si |o si |puede ser |podria ser |tambien |en otro )', t))


def es_rectificacion(texto):
    t = normalizar_dialogo(texto)
    return bool(re.search(r'\b(?:me (?:confundi|equivoque)|quise decir|queria decir|me (?:refiero|referia)|era por|no era|no es eso)\b', t)
                or re.match(r'^(?:no|era|mejor|perdon)\b', t))


def evidencia_contextual(texto, macro, pregunta=None):
    """Evidencia del caso actual antes de que ML clasifique una frase aislada."""
    t = normalizar_dialogo(texto)
    if extraer_atributos(t, macro, pregunta) or nlp.resolver_grupo_macro(macro, t):
        return True
    if nlp.coincidencias_intencion_macro(macro, t):
        return True
    return bool(proponer(macro, t, nlp.INTENCIONES_MACRO[macro]['opciones']))


def tema_refina_contexto(tema, contexto, texto):
    """Una familia amplia no desplaza el procedimiento que estamos precisando.

    «Modalidad B de habilitación» sigue siendo respuesta a modificación de HU;
    «cambiar de giro» sigue siendo el giro del puesto si no menciona otra licencia.
    """
    if not tema or tema == contexto:
        return True
    if tema == 'consultar_habilitacion_urbana' and any(p in contexto for p in (
        'habilitacion', 'terreno_rustico', 'regularizacion_obras',
    )):
        if re.search(r'\b(?:aprobar|sacar|solicitar|obtener) (?:una|la) habilitacion urbana\b', texto):
            return False
        if re.search(r'\bmodalidad\b', texto) and not any('modalidad' in p for p in PERFILES.get(contexto, {}).values()):
            return False
        return True
    if tema == 'consultar_lotes_urbanos' and contexto == 'consultar_independizacion_terreno_rustico':
        return True
    if tema in {'consultar_licencia_construccion', 'consultar_habilitacion_urbana'} and contexto == 'consultar_prorroga_revalidacion_licencia':
        from backend.chatbot.politica import solicitud_completa
        return not solicitud_completa(texto) or bool(re.search(r'\b(?:prorrog\w*|revalid\w*|vencid\w*|vigente)\b', texto))
    if tema == 'consultar_licencia_construccion' and any(p in contexto for p in (
        'edificacion', 'conformidad_obra', 'regularizacion_obras',
    )):
        from backend.chatbot.politica import solicitud_completa
        return not solicitud_completa(texto)
    if tema == 'consultar_licencia_edificacion_no_vivienda' and contexto == 'consultar_licencia_edificacion_estado':
        return True
    if tema == 'consultar_tramite_vehicular' and contexto == 'consultar_gestion_flota_vehicular':
        return not re.search(r'\b(?:tarjeta|datos|duplicado|perdi|sustitucion|dar de baja|empadronar)\b', texto)
    if tema == 'consultar_licencia_funcionamiento' and contexto in {
        'consultar_licencia_cesionario', 'consultar_gestion_licencia',
    }:
        if contexto == 'consultar_gestion_licencia' and re.search(r'\b(?:riesgo|abrir|apertura|restaurante|bodega|bodegas)\b', texto):
            return False
        return True
    if tema == 'consultar_gestion_licencia' and contexto in {
        'consultar_puesto_mercado', 'consultar_certificacion_sanitaria',
    } and not re.search(r'\blicencia\b', texto):
        return True
    return False


def tema_explicito(texto):
    """Señales de cambio de asunto; no confundir una respuesta breve con otro trámite."""
    t = normalizar_dialogo(texto)
    familias = [
        (r'\b(?:vereda|rampa|berma|via publica|obra publica terminada|termine la obra publica|romper la pista|abrir la pista)\b', 'consultar_obras_via_publica'),
        (r'\b(?:revalidar|revalidacion|prorrogar|prorroga)\b.*\b(?:licencia|habilitacion|construccion|edificacion)\b', 'consultar_prorroga_revalidacion_licencia'),
        (r'\b(?:colegio estatal|colegio publico|escuela publica|hospital publico|universidad nacional|viviendas del estado)\b', 'consultar_licencia_edificacion_estado'),
        (r'\b(?:dividir|subdividir|partir|fraccionar|juntar|unir|acumular)\b.*\b(?:lote|lotes|terreno|terrenos)\b', 'consultar_lotes_urbanos'),
        (r'\b(?:terreno.*chacra|terreno rustico|terreno agricola|parcelar|lotizar)\b', 'consultar_independizacion_terreno_rustico'),
        (r'\b(?:regularizar|regularizacion)\b.*\b(?:casa|construccion|edificacion|obra)\b|\b(?:casa|construccion|edificacion)\b.*\b(?:regularizar|(?:hice|construi|edifique).*sin licencia)\b', 'consultar_regularizacion_obras'),
        (r'\blicencia\b.*\b(?:vencio|vencida|vencido)\b|\b(?:vencio|vencida)\b.*\blicencia\b', 'consultar_prorroga_revalidacion_licencia'),
        (r'\b(?:segundo|tercer|cuarto|otro|nuevo) piso\b.*\b(?:casa|vivienda)\b', 'consultar_licencia_ampliacion_remodelacion'),
        (r'\b(?:flota|permiso de operacion|paradero)\b.*\b(?:mototaxi|transporte|empresa|asociacion)\b|\b(?:empresa|asociacion)\b.*\b(?:mototaxi|flota|permiso de operacion)\b', 'consultar_gestion_flota_vehicular'),
        (r'\b(?:certificacion sanitaria|certificado sanitario|carnet sanitario)\b', 'consultar_certificacion_sanitaria'),
        (r'\b(?:conformidad de obra|declaratoria de edificacion|ya termine.*(?:casa|construir|obra)|inscribir mi (?:casa|edificacion))\b', 'consultar_conformidad_obra'),
        (r'\b(?:casarme|casarnos|matrimonio|boda|casar)\b', 'consultar_matrimonio_civil'),
        (r'\b(?:divorcio|divorciarme|separacion convencional)\b', 'consultar_divorcio'),
        (r'\b(?:licencia de funcionamiento|licencia.*(?:bodegas?|tienda|negocio|restaurante)|abrir mi negocio|abrir una tienda|(?:abrir|poner|tengo) una? (?:discoteca|peluqueria|restaurante|botica|gimnasio|grifo|clinica))\b', 'consultar_licencia_funcionamiento'),
        (r'\b(?:cambio de giro|transferir la licencia|cese de actividades|duplicado de licencia|pasar mi licencia|(?:perdi|duplicado|cerrar|cerre|cambiar el giro).*(?:licencia|negocio|tienda)|licencia.*(?:perdi|robaron|duplicado))\b', 'consultar_gestion_licencia'),
        (r'\b(?:alquilar un local.*licencia de otro|licencia de cesionario|soy cesionario)\b', 'consultar_licencia_cesionario'),
        (r'\b(?:numeracion|numero de puerta)\b', 'consultar_numeracion_municipal'),
        (r'\b(?:catastro|catastral)\b', 'consultar_catastro_predial'),
        (r'\b(?:conexion de agua|conectar (?:el |la )?(?:agua|desague)|conexion de desague)\b', 'consultar_conexion_agua'),
        (r'\b(?:mototaxi|tarjeta de operatividad|mi vehiculo|mi moto)\b|\b(?:moto|vehiculo)\b.*\b(?:baja|sustitucion)\b', 'consultar_tramite_vehicular'),
        (r'\b(?:puesto de mercado|puesto del mercado|mi puesto|puesto\b.*\bmercado)\b', 'consultar_puesto_mercado'),
        (r'\b(?:habilitacion urbana|habilitar un terreno|habilitar mi terreno)\b', 'consultar_habilitacion_urbana'),
        (r'\b(?:demoler|demolicion|tirar abajo|botar mi casa)\b', 'consultar_licencia_demolicion'),
        (r'\b(?:licencia de construccion|permiso para construir|papel para construir|(?:construir|edificar|levantar|hacer un edificio)\b.*\b(?:mi casa|una casa|la casa|vivienda|departamentos|mi lote))\b', 'consultar_licencia_construccion'),
        (r'\b(?:ampliar|remodelar|agrandar)\b.*\b(?:casa|vivienda|edificio)\b', 'consultar_licencia_ampliacion_remodelacion'),
        (r'\b(?:construir|edificar)\b.*\b(?:mercado|local comercial|colegio|clinica|hotel|estadio|fabrica|industria|taller|oficinas?|banco|deposito|almacen|templo|iglesia|hospital|universidad)\b', 'consultar_licencia_edificacion_no_vivienda'),
        (r'\b(?:cerco|cercar)\b', 'consultar_licencia_cerco'),
        (r'\b(?:itse|inspeccion de seguridad|certificado de defensa civil)\b', 'consultar_itse'),
        (r'\b(?:perro|canino|mascota canina)\b', 'consultar_registro_canino'),
        (r'\b(?:letrero|publicidad exterior|anuncio)\b', 'consultar_publicidad_exterior'),
        (r'\b(?:fibra optica|telecomunicaciones|radiocomunicacion|antena de celular|instalar una antena)\b', 'consultar_telecomunicaciones'),
        (r'\b(?:terreno (?:agricola|rustico)|parcelar)\b', 'consultar_independizacion_terreno_rustico'),
        (r'\b(?:recurso administrativo|impugnar|muni.*denego|municipalidad.*denego|reclamar.*deneg|apelacion|reconsideracion|no estoy de acuerdo.*(?:resolvieron|resolucion|decision))\b', 'consultar_recurso_administrativo'),
        (r'\b(?:feria|circo|juegos mecanicos|concierto|espectaculo)\b', 'consultar_evento_publico'),
    ]
    encontrados = [macro for patron, macro in familias if re.search(patron, t)]
    # Los términos de una fase específica prevalecen sobre su familia general.
    for preferida, generales in [('consultar_conformidad_obra', {'consultar_licencia_construccion'}),
                                ('consultar_obras_via_publica', {'consultar_conformidad_obra', 'consultar_licencia_construccion'}),
                                ('consultar_conexion_agua', {'consultar_obras_via_publica'}),
                                ('consultar_prorroga_revalidacion_licencia', {'consultar_licencia_construccion', 'consultar_habilitacion_urbana'}),
                                ('consultar_regularizacion_obras', {'consultar_licencia_construccion'}),
                                ('consultar_licencia_edificacion_no_vivienda', {'consultar_licencia_construccion'}),
                                ('consultar_licencia_ampliacion_remodelacion', {'consultar_licencia_construccion'}),
                                ('consultar_independizacion_terreno_rustico', {'consultar_lotes_urbanos'}),
                                ('consultar_gestion_flota_vehicular', {'consultar_tramite_vehicular'}),
                                ('consultar_licencia_edificacion_estado', {'consultar_licencia_edificacion_no_vivienda'}),
                                ('consultar_itse', {'consultar_licencia_funcionamiento'}),
                                ('consultar_gestion_licencia', {'consultar_licencia_funcionamiento'}),
                                ('consultar_licencia_cesionario', {'consultar_licencia_funcionamiento'})]:
        if preferida in encontrados:
            encontrados = [m for m in encontrados if m not in generales]
    return encontrados[0] if len(set(encontrados)) == 1 else None


def es_detalle_del_caso(texto, macro):
    """No interpretar sustantivos ajenos como respuestas a una pregunta municipal."""
    t = normalizar_dialogo(texto)
    vocabulario = set("""yo es soy son seria sera quiero necesito para por de del la el los las un una mi mis
    me a al en con sin si no aqui aca esto eso ese esa dentro fuera mismo otra otro mismo nomas
    ya tengo tiene esta esta es va van llevar lleva llevara tener tiene ninguna ningun ninguna luz
    privado privada particulares particular compartido compartida vecinos sus nuestro nuestra
    documento papel tipo riesgo modal modalidad es el creo que solo poquito pequena grande
    primero primera nuevo nueva empezar comenzar hacerlo hacer solicitar obtener sacar""".split())
    for datos in nlp.INTENCIONES_MACRO[macro]['opciones'].values():
        fuentes = [datos['etiqueta'], *datos.get('frases', ()), *datos.get('palabras', ())]
        fuentes.extend(frase for grupo in datos.get('todas', ()) for frase in grupo)
        for fuente in fuentes:
            vocabulario.update(normalizar_dialogo(fuente).split())
    return bool(t) and set(t.split()) <= vocabulario
