"""Consultas naturales de evaluación; no se leen frases del resolver para crearlas."""

from pathlib import Path


def cargar_consultas():
    casos = []
    macro = None
    for linea in Path(__file__).with_suffix('.txt').read_text(encoding='utf-8').splitlines():
        if not linea or linea.startswith('#'):
            continue
        if linea.startswith('['):
            macro = linea[1:-1]
            continue
        clave, *frases = linea.split('|')
        assert len(frases) == 5, (macro, clave)
        casos.extend((macro, clave, frase) for frase in frases)

    def agregar(macro, clave, plantillas, **variables):
        casos.extend(('consultar_' + macro, clave, plantilla.format(**variables)) for plantilla in plantillas)

    for clave, modalidad in zip('abc', 'BCD'):
        agregar('anteproyecto_consulta', clave, [
            'Quiero consultar un anteproyecto de modalidad {m}.',
            'Necesito aprobar mi anteproyecto en modalidad {m}.',
            'Deseo presentar un anteproyecto para modalidad {m}.',
            'Quiero los requisitos del anteproyecto de modalidad {m}.',
            'Necesito tramitar la consulta de anteproyecto de modalidad {m}.',
        ], m=modalidad)
    for clave, modalidad in zip('abc', 'BCD'):
        agregar('modificacion_proyecto_edificacion', clave, [
            'Quiero modificar el proyecto antes de la licencia, modalidad {m}.',
            'Necesito modificar antes de que me den la licencia de modalidad {m}.',
            'Deseo cambiar el proyecto sin licencia emitida, modalidad {m}.',
            'Aún no me dan la licencia y quiero modificar, modalidad {m}.',
            'Quiero cambiar el proyecto antes de obtener la licencia de modalidad {m}.',
        ], m=modalidad)
    for claves, plantillas in [
        ('defg', [
            'Quiero un cambio pequeño después de la licencia, modalidad {m}.',
            'Necesito registrar un cambio menor de modalidad {m}.',
            'Deseo una modificación no sustancial de modalidad {m}.',
            'Quiero autorizar cambios menores de modalidad {m}.',
            'Necesito un ajuste pequeño de mi proyecto de modalidad {m}.',
        ]),
        ('hijk', [
            'Quiero un cambio grande después de la licencia, modalidad {m}.',
            'Necesito registrar un cambio sustancial de modalidad {m}.',
            'Deseo una modificación sustancial de modalidad {m}.',
            'Quiero autorizar cambios grandes de modalidad {m}.',
            'Necesito una modificación importante de mi proyecto de modalidad {m}.',
        ]),
    ]:
        for clave, modalidad in zip(claves, 'ABCD'):
            agregar('modificacion_proyecto_edificacion', clave, plantillas, m=modalidad)

    sin_cambios = [
        'Quiero {gestion} de mi obra sin cambios, modalidad {m}.',
        'Necesito {gestion}, quedó igual a los planos, modalidad {m}.',
        'Deseo {gestion}, la obra está sin variaciones, modalidad {m}.',
        'Quiero {gestion}, quedó tal cual el proyecto de modalidad {m}.',
        'Necesito {gestion} de la obra sin modificaciones, modalidad {m}.',
    ]
    con_cambios = [
        'Quiero {gestion} de mi obra con cambios, modalidad {m}.',
        'Necesito {gestion}, quedó distinto al plano, modalidad {m}.',
        'Deseo {gestion}, la obra tiene variaciones y quedó con variaciones, modalidad {m}.',
        'Quiero {gestion} de la obra con modificaciones de modalidad {m}.',
        'Necesito {gestion}, quedó diferente al proyecto de modalidad {m}.',
    ]
    agregar('conformidad_obra', 'a', sin_cambios, gestion='conformidad', m='A')
    agregar('conformidad_obra', 'b', sin_cambios, gestion='conformidad', m='B')
    for clave, modalidad in zip('cdef', 'ABCD'):
        agregar('conformidad_obra', clave, con_cambios, gestion='conformidad', m=modalidad)
    agregar('conformidad_obra', 'g', [
        'Quiero la declaración municipal de edificación terminada.',
        'Necesito la declaración municipal de obra terminada.',
        'Deseo solicitar solo la declaración municipal.',
        'Quiero requisitos de la declaración municipal de edificación terminada.',
        'Necesito tramitar solo la declaración municipal para mi edificio.',
    ])
    for macro, pares, gestion in [
        ('conformidad_obra_anticipada', [('abc', 'BCD', sin_cambios), ('def', 'BCD', con_cambios)], 'conformidad anticipada del casco no habitable'),
        ('recepcion_obras_habilitacion', [('abcd', 'ABCD', sin_cambios), ('efgh', 'ABCD', con_cambios)], 'recepción de obras de habilitación'),
    ]:
        for claves, modalidades, plantillas in pares:
            for clave, modalidad in zip(claves, modalidades):
                agregar(macro, clave, plantillas, gestion=gestion, m=modalidad)
    agregar('recepcion_obras_habilitacion', 'i', [
        'Quiero una recepción parcial de las obras de habilitación.',
        'Necesito recibir una etapa de mi habilitación.',
        'Deseo recibir solo una etapa ya construida.',
        'Quiero la recepción de una etapa terminada.',
        'Necesito la recepción de solo la primera etapa.',
    ])
    for macro, tipo in [('proyecto_integral_edificacion', 'edificación'), ('proyecto_integral_habilitacion', 'habilitación')]:
        for clave, modalidad in zip('ab', 'CD'):
            agregar(macro, clave, [
                'Quiero solo el proyecto integral de {tipo}, modalidad {m}.',
                'Necesito aprobar solamente el proyecto integral de {tipo}, modalidad {m}.',
                'Deseo aprobar únicamente el proyecto integral de {tipo}, modalidad {m}.',
                'Quiero solo aprobar el proyecto de {tipo} en modalidad {m}.',
                'Necesito aprobar el proyecto integral de {tipo} sin licencia de etapa, modalidad {m}.',
            ], tipo=tipo, m=modalidad)
        for clave, modalidad in zip('cd', 'CD'):
            agregar(macro, clave, [
                'Quiero aprobar proyecto y licencia de {tipo} de modalidad {m}.',
                'Necesito el proyecto integral y la licencia de {tipo} de modalidad {m}.',
                'Deseo proyecto integral con licencia de {tipo} de modalidad {m}.',
                'Quiero el proyecto junto con la licencia de {tipo} de modalidad {m}.',
                'Necesito proyecto y la licencia de etapa de {tipo} de modalidad {m}.',
            ], tipo=tipo, m=modalidad)
        agregar(macro, 'e', [
            'Quiero licencia de etapa de un proyecto integral aprobado de {tipo}.',
            'Ya aprobaron el proyecto integral de {tipo} y necesito una etapa.',
            'Deseo licencia de etapa de un proyecto integral ya aprobado de {tipo}.',
            'Ya tengo aprobado el proyecto de {tipo} y quiero una etapa.',
            'Necesito una etapa de un proyecto aprobado anteriormente de {tipo}.',
        ], tipo=tipo)
    agregar('proyecto_integral_edificacion', 'f', [
        'Quiero modificar una etapa de un proyecto integral aprobado.',
        'Necesito cambiar el proyecto de una etapa de edificación.',
        'Deseo la modificación de una etapa de un proyecto integral.',
        'Quiero modificar el proyecto integral de una etapa ya aprobada.',
        'Necesito modificar una etapa de edificación con plazo vencido.',
    ])
    for clave, modalidad in zip('abcd', 'ABCD'):
        agregar('modificacion_habilitacion_urbana', clave, [
            'Quiero modificar una habilitación urbana de modalidad {m}.',
            'Necesito cambiar mi proyecto de habilitación, modalidad {m}.',
            'Deseo tramitar una modificación de habilitación urbana en modalidad {m}.',
            'Quiero los requisitos para modificar habilitación de modalidad {m}.',
            'Necesito autorizar cambios de habilitación de modalidad {m}.',
        ], m=modalidad)
    for clave, tipo, accion in [('a', 'edificación', 'prorrogar'), ('b', 'construcción', 'revalidar'), ('c', 'habilitación urbana', 'prorrogar'), ('d', 'habilitación urbana', 'revalidar')]:
        agregar('prorroga_revalidacion_licencia', clave, [
            'Quiero {accion} mi licencia de {tipo}.',
            'Necesito {accion} la autorización de {tipo}.',
            'Deseo {accion} una licencia de {tipo}.',
            'Quiero los requisitos para {accion} mi licencia de {tipo}.',
            'Necesito tramitar la solicitud para {accion} mi licencia de {tipo}.',
        ], accion=accion, tipo=tipo)
    return casos


CASOS = cargar_consultas()
