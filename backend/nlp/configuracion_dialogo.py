"""Reglas exactas y textos breves del diálogo; no intervienen en el modelo ML.

Cada alternativa conserva su clave e identificadores históricos. Las expresiones
son frases completas o palabras exactas, nunca raíces ni similitud ortográfica.
"""

from itertools import product


def _lista(texto):
    return [parte.strip() for parte in texto.split("|") if parte.strip()]


def _combinaciones(*condiciones):
    return [list(grupo) for grupo in product(*[_lista(c) for c in condiciones])]


def preparar_macros(macros):
    macros["consultar_gestion_licencia"] = {
        "opciones": {k: {"id_tramite": codigo} for k, codigo in zip("abcd", ("T_002", "T_004", "T_005", "T_006"))},
        "frases_no_seguro": ["no se", "no lo se", "no estoy seguro", "no tengo idea", "ni idea"],
        "mensaje_no_seguro": "Cuéntame si quieres cambiar el giro, transferir, cerrar o duplicar tu licencia.",
    }
    # El menú de eventos contenía accidentalmente las opciones de divorcio.
    macros["consultar_evento_publico"]["opciones"]["a"]["id_tramite"] = "T_030"
    macros["consultar_evento_publico"]["opciones"]["b"]["id_tramite"] = "T_062"

    def r(macro, clave, etiqueta, frases="", *, todas=(), excluir="", palabras=""):
        opcion = macros["consultar_" + macro]["opciones"][clave]
        opcion.update(etiqueta=etiqueta, frases=_lista(frases), todas=list(todas),
                      excluir=_lista(excluir), palabras=set(_lista(palabras)))

    r("matrimonio_civil", "a", "Municipalidad en horario habitual", "dentro de la municipalidad|en la municipalidad|en la muni|de la muni|local municipal|horario normal|horario de trabajo|horario habitual", excluir="fuera de horario|fuera del horario|noche|sabado|domingo|feriado|alcalde|comunitario|comunitaria")
    r("matrimonio_civil", "b", "Local público dentro del distrito", "local publico dentro del distrito|otro local dentro del distrito|colegio dentro del distrito|local publico de jlo|local publico dentro de jlo")
    r("matrimonio_civil", "c", "Municipalidad fuera de horario", "fuera de horario|fuera del horario|fuera de hora|fin de semana|horario nocturno", palabras="sabado|domingo|feriado|noche")
    r("matrimonio_civil", "d", "Local público fuera del distrito", "fuera del distrito|otro distrito|otra ciudad|otra provincia|fuera de jlo")
    r("matrimonio_civil", "e", "Domicilio dentro del distrito", "en mi casa|en casa|mi domicilio|en el domicilio|en mi hogar", palabras="domicilio")
    r("matrimonio_civil", "f", "Ceremonia con el alcalde", "oficiada por el alcalde|que nos case el alcalde|con el alcalde", palabras="alcalde")
    r("matrimonio_civil", "g", "Matrimonio comunitario", "con otras parejas|matrimonio colectivo|boda grupal", palabras="comunitario|comunitaria|colectivo|masivo|grupal")
    macros["consultar_matrimonio_civil"]["opciones"]["a"]["confirmacion"] = "Perfecto, para casarte en la municipalidad necesitas esto:"
    macros["consultar_matrimonio_civil"]["mensaje_no_seguro"] = "No hay apuro. Cuéntame dónde deseas casarte y en qué horario."

    r("conexion_agua", "natural", "Persona natural", "persona natural|a mi nombre|a nombre propio|para mi casa|para mi vivienda|soy particular", palabras="natural|particular")
    r("conexion_agua", "juridica", "Empresa o persona jurídica", "persona juridica|para mi empresa|a nombre de la empresa|razon social|para una empresa", palabras="juridica|empresa|constructora")
    negativas = "sin luz|sin luces|sin led|sin neon|no tiene luz|no lleva luz|no es luminoso|no es iluminado"
    r("publicidad_exterior", "a", "Anuncio sin iluminación", negativas + "|anuncio simple|aviso simple|letrero simple|banner sin iluminacion|sin iluminacion")
    r("publicidad_exterior", "b", "Anuncio luminoso o iluminado", "con luz|con luces|con led|con neon|aviso luminoso|anuncio iluminado|letrero luminoso|tiene luz", excluir=negativas)
    r("certificacion_sanitaria", "a", "Obtener o renovar certificado", "primera certificacion|primera vez|sacar mi certificacion|sacar la certificacion|sacar mi certificado|renovar la certificacion|renovar mi certificado", palabras="renovar|renovacion|obtener", excluir="duplicado|perdi|extravio|baja")
    r("certificacion_sanitaria", "b", "Duplicado del certificado", "se me perdio|me robaron|otra copia|certificado deteriorado", palabras="duplicado|perdi|extravio|extravie|malogro")
    r("certificacion_sanitaria", "c", "Baja del certificado", "dar de baja|cerrar mi negocio|cierro mi negocio|anular la certificacion|cancelar mi certificado", palabras="baja|cese")
    negativas = "no es peligroso|no es peligrosa|no es de raza peligrosa|no peligroso|no peligrosa|raza no peligrosa"
    r("registro_canino", "a", "Can de raza no peligrosa", negativas, palabras="mestizo|criollo|comun")
    r("registro_canino", "b", "Can potencialmente peligroso", "raza peligrosa|potencialmente peligroso|bull terrier|fila brasileno", palabras="pitbull|rottweiler|dogo|bullterrier", excluir=negativas)
    r("evento_publico", "a", "Espectáculo con público", "evento con publico|espectaculo publico|evento musical|show con publico", palabras="concierto|festival|espectaculo")
    r("evento_publico", "b", "Feria, circo o juegos mecánicos", "juegos mecanicos|instalar una feria|instalar un circo", palabras="feria|ferias|circo|circos")
    r("tramite_vehicular", "a", "Empadronar vehículo nuevo", "vehiculo nuevo|mototaxi nueva|mototaxi nuevo|moto nueva|por primera vez", palabras="empadronar|registrar|empadronamiento|inscribir", excluir="duplicado|renovar|cambio de datos")
    r("tramite_vehicular", "b", "Renovar tarjeta de operatividad", "tarjeta vencida|se vencio|actualizar la vigencia|renovar mi tarjeta|renovar la tarjeta", palabras="renovar|renovacion|vencio", excluir="duplicado|datos del propietario")
    r("tramite_vehicular", "c", "Duplicado de tarjeta", "se me perdio|me robaron|otra copia|tarjeta extraviada", palabras="duplicado|perdi|extravio|extravie|robada")
    r("tramite_vehicular", "d", "Baja o sustitución de unidad", "dar de baja|cambiar de unidad|cambiar la unidad|otra unidad|cambiar mi moto|cambiar mi vehiculo", palabras="baja|reemplazar|sustituir|chatarrear")
    r("tramite_vehicular", "e", "Cambiar datos del titular", "cambiar los datos|cambio de datos|modificar los datos|cambiar el nombre|razon social|nombre del propietario|nombre del titular|datos del propietario|datos de mi tarjeta")
    r("gestion_flota_vehicular", "a", "Permiso nuevo de operación", "permiso nuevo|nuevo permiso|primera autorizacion|primer permiso|por primera vez", excluir="renovar|renovacion|incrementar|paradero")
    r("gestion_flota_vehicular", "b", "Renovar permiso de operación", "permiso vencido|permiso por vencer|renovar el permiso|renovar mi permiso|renovacion del permiso", palabras="renovar|renovacion")
    r("gestion_flota_vehicular", "c", "Incrementar flota", "mas vehiculos|agregar unidades|aumentar la flota|incrementar mi flota|ampliar la flota", palabras="incrementar|incremento|aumentar|agregar")
    r("gestion_flota_vehicular", "d", "Autorización de paradero", "zona de espera|punto de espera|usar un paradero", palabras="paradero|paraderos")
    r("divorcio", "a", "Separación convencional inicial", "primera separacion|iniciar la separacion|separacion por mutuo acuerdo|mutuo acuerdo|no tengo la separacion|aun no tengo separacion|primer paso|primera vez", excluir="ya tengo|ya pasaron|ulterior|ya esta aprobada")
    r("divorcio", "b", "Divorcio ulterior", "ya tengo la separacion|ya tengo mi separacion|ya pasaron dos meses|ya pasaron 2 meses|separacion aprobada|divorcio final|divorcio definitivo", palabras="ulterior")
    r("puesto_mercado", "a", "Conseguir puesto o empadronarse", "primera vez|puesto nuevo|conseguir un puesto|conseguir mi puesto|inscribirme en el mercado", palabras="empadronarme|empadronar|empadronamiento|conducir")
    r("puesto_mercado", "b", "Renovar puesto", "puesto por vencer|puesto vencido", palabras="renovar|renovacion|vencio|vence|prorroga")
    r("puesto_mercado", "c", "Sucesión por fallecimiento", "familiar fallecido|familiar fallecida|fallecio mi padre|fallecio mi madre", palabras="fallecio|fallecido|fallecida|heredar|herencia|murio")
    r("puesto_mercado", "d", "Puesto abandonado o vacante", "puesto vacio|puesto libre|puesto sin ocupar", palabras="abandonado|abandono|vacante|revertido|desocupado")
    r("puesto_mercado", "e", "Remodelar o reparar puesto", "arreglar el techo|arreglar mi puesto", palabras="remodelar|reparar|remodelacion|mantenimiento|pintar")
    r("puesto_mercado", "f", "Cambiar giro del puesto", "cambiar lo que vendo|vender otra cosa|cambiar de giro|cambio de giro|cambiar de rubro", palabras="giro|rubro")
    r("numeracion_municipal", "a", "Certificar número existente", "certificado de numeracion|certificar el numero|ya existe|ya esta construida|ya esta construido|casa existente|numero actual", palabras="certificado", excluir="proyecto aprobado|asignacion")
    r("numeracion_municipal", "b", "Asignar número a proyecto aprobado", "proyecto aprobado|construccion aprobada|asignacion de numeracion|asignen numero|cada departamento|cada local|licencia de edificacion", palabras="asignacion|condominio")
    r("catastro_predial", "a", "Certificado catastral positivo", "ya tiene codigo|si tiene codigo|ya esta registrado|ya esta registrada|ya cuenta con codigo|certificado positivo", palabras="positivo")
    r("catastro_predial", "b", "Certificado catastral negativo", "no tiene codigo|no esta registrado|no esta registrada|no figura|no cuenta con codigo|sin codigo|certificado negativo", palabras="negativo")
    r("catastro_predial", "c", "Actualizar datos catastrales", "actualizar los datos|actualizar mi catastro|corregir datos|datos errados|modificar los datos", palabras="actualizar|actualizacion|corregir")
    r("recurso_administrativo", "a", "Reconsideración con nueva prueba", "nueva prueba|nuevas pruebas|prueba nueva|pruebas nuevas|documento nuevo|nuevo documento|tengo una prueba", palabras="reconsideracion|reconsiderar", excluir="no tengo|sin pruebas|sin prueba|no hay pruebas|no hay prueba")
    r("recurso_administrativo", "b", "Apelación por interpretación o derecho", "no tengo pruebas|no tengo prueba|sin pruebas|sin prueba|cuestion de ley|puro derecho|interpretaron mal|mala interpretacion|revision por el superior", palabras="apelacion|apelar|apelo")

    r("habilitacion_urbana", "a", "Inversión pública o concesión", "inversion publica|obra publica|infraestructura publica|servicio publico|servicios publicos|asociacion publico privada|concesion publica", excluir="bono familiar|programa de vivienda")
    r("habilitacion_urbana", "b", "Vivienda estatal con bono", "bono familiar habitacional|bono familiar|bono habitacional|programa de vivienda del estado|programa estatal de vivienda|reubicar beneficiarios", palabras="bfh")
    r("habilitacion_urbana", "c", "Residencial hasta cinco hectáreas", "residencial de hasta cinco hectareas|residencial de hasta 5 hectareas|residencial menor de cinco hectareas|residencial menor de 5 hectareas|unico lote residencial|un solo lote residencial|terreno residencial sin habilitar", excluir="modificar|modificacion|con garantia|venta garantizada|viviendas edificadas|colinda|patrimonio|industria")
    r("habilitacion_urbana", "d", "Modificar proyecto aprobado por etapas", "modificar mi proyecto aprobado|modificar un proyecto aprobado|modificacion de proyecto aprobado|cambiar una etapa aprobada|modificar proyecto integral|proyecto aprobado con plazo vencido")
    r("habilitacion_urbana", "e", "Venta garantizada de lotes", "venta garantizada|lotes con garantia|vender lotes con garantia|vender los lotes con garantia|venta de lotes garantizada")
    r("habilitacion_urbana", "f", "Vender viviendas ya edificadas", "construir las viviendas para vender|construir viviendas para vender|venta de viviendas edificadas|vender casas construidas|vender las viviendas edificadas|urbanizacion con casas construidas")
    r("habilitacion_urbana", "g", "Terreno en área protegida", "dentro de patrimonio cultural|dentro de una zona arqueologica|dentro de un area natural protegida|en un ecosistema fragil|dentro de un area protegida|en zona de amortiguamiento")
    r("habilitacion_urbana", "h", "Reurbanizar zona existente", "mover vias|reubicar vias|reorganizar calles|recomponer la trama urbana", palabras="reurbanizar|reurbanizacion|redimensionamiento")
    r("habilitacion_urbana", "i", "Terreno sin colindancia urbana", "no colinda con zona urbana|no colinda con la zona urbana|sin colindar con zona urbana|terreno aislado|lejos de la ciudad|requiere planeamiento integral")
    r("habilitacion_urbana", "j", "Colindante con área protegida", "colinda con zona arqueologica|colinda con una zona arqueologica|colinda con patrimonio cultural|colinda con un area natural|junto a una zona arqueologica|junto a un area protegida")
    r("habilitacion_urbana", "k", "Industria, comercio u otros usos", "uso industrial|uso comercial|parque industrial|para industria|para comercio|usos especiales|habilitacion comercial")
    r("lotes_urbanos", "a", "Subdividir lote", "dividir mi lote|dividir un lote|partir mi lote|separar mi lote|crear sublotes", palabras="subdivision|subdividir|fraccionar|sublotes")
    r("lotes_urbanos", "b", "Acumular lotes", "juntar dos lotes|unir mis lotes|en uno solo|un solo lote|una sola unidad", palabras="acumulacion|acumular|fusionar|juntar")

    # El nivel de riesgo debe ser declarado: el giro por sí solo no lo prueba.
    riesgos = ("riesgo bajo|bajo riesgo", "riesgo medio|riesgo moderado", "riesgo alto", "riesgo muy alto")
    for clave, riesgo, etiqueta in zip("abc", riesgos[1:], ("Riesgo medio", "Riesgo alto", "Riesgo muy alto")):
        r("licencia_cesionario", clave, etiqueta, riesgo)
    for clave, riesgo, etiqueta in zip("abcd", riesgos, ("Riesgo bajo", "Riesgo medio", "Riesgo alto", "Riesgo muy alto")):
        r("licencia_funcionamiento", clave, etiqueta, riesgo)
    r("licencia_funcionamiento", "e", "Licencia corporativa", "licencia corporativa|galeria completa|mercado completo|centro comercial completo|junta de propietarios")

    renovaciones = "renovar|renovacion|renuevo|vencio|vencido|vencida|por vencer"
    duplicados = "duplicado|perdi|extravio|extravie|me robaron|otra copia"
    for clave, riesgo, etiqueta in zip("abcd", riesgos, ("Inicial: riesgo bajo", "Inicial: riesgo medio", "Inicial: riesgo alto", "Inicial: riesgo muy alto")):
        r("itse", clave, etiqueta, riesgo, excluir=renovaciones + "|" + duplicados)
    for clave, riesgo, etiqueta in zip("efgh", riesgos, ("Renovar: riesgo bajo", "Renovar: riesgo medio", "Renovar: riesgo alto", "Renovar: riesgo muy alto")):
        r("itse", clave, etiqueta, todas=_combinaciones(renovaciones, riesgo), excluir=duplicados)
    r("itse", "i", "Duplicado del certificado ITSE", duplicados)

    r("licencia_construccion", "a", "Unifamiliar hasta ciento veinte metros", "unifamiliar de hasta 120|unifamiliar de hasta ciento veinte|una sola vivienda de 120|casa de 120|casa de ciento veinte|unica edificacion de 120")
    r("licencia_construccion", "b", "Vivienda hasta cinco pisos", "hasta cinco pisos|hasta 5 pisos|cuatro pisos|tres pisos|3 pisos|4 pisos|menos de 3000", excluir="uso mixto|comercio y vivienda|patrimonio|historica")
    r("licencia_construccion", "c", "Vivienda mayor de cinco pisos", "mas de cinco pisos|mas de 5 pisos|mas de 3000|seis pisos|6 pisos|siete pisos|mas de tres mil", excluir="uso mixto|comercio y vivienda|patrimonio")
    r("licencia_construccion", "d", "Vivienda y comercio", "uso mixto|vivienda y comercio|comercio y vivienda|tienda abajo|negocio en el primer piso|tienda y vivienda|departamentos encima", excluir="patrimonio")
    r("licencia_construccion", "e", "Predio patrimonio cultural", "patrimonio cultural|monumento historico|casona historica|casa historica|predio historico")
    r("licencia_ampliacion_remodelacion", "a", "Ampliar vivienda hasta 200 m²", "ampliacion hasta 200|ampliar hasta 200|ampliacion de hasta 200|ampliar mi casa hasta 200|ampliacion hasta doscientos|ampliar mi casa sin superar 200")
    r("licencia_ampliacion_remodelacion", "b", "Remodelar sin cambiar estructura", "sin tocar la estructura|sin modificar la estructura|sin cambiar la estructura|sin tocar columnas|solo acabados|sin aumentar el area", excluir="obra menor")
    r("licencia_ampliacion_remodelacion", "c", "Obra menor", "obra menor|obras menores|obra pequena|pequenas mejoras|remodelacion menor|ampliacion pequena")
    r("licencia_ampliacion_remodelacion", "d", "Vivienda con cambios estructurales", "cambiar la estructura|modificar la estructura|cambio estructural|aumentar el area techada|cambiar el uso de mi vivienda|columnas y vigas", excluir="sin cambiar|sin modificar|sin tocar|comercial|oficinas|multifamiliar|fabrica|mercado|colegio|clinica|hotel|terminal")
    r("licencia_ampliacion_remodelacion", "e", "Remodelar edificio comercial o multifamiliar", "edificio comercial|edificio de oficinas|vivienda multifamiliar|local de varios pisos|edificio grande|centro comercial")
    r("licencia_ampliacion_remodelacion", "f", "Remodelar industria o servicios especiales", "fabrica|industria|mercado|colegio|clinica|hotel|terminal|hospital|estadio")
    r("licencia_demolicion", "a", "Total hasta tres pisos", "hasta tres pisos|hasta 3 pisos|dos pisos|un piso|tres pisos|3 pisos|1 piso|2 pisos", excluir="parcial|una parte|con sotano|con semisotano|con explosivos|dinamita")
    r("licencia_demolicion", "b", "Total hasta cinco pisos o sótano", "cinco pisos|5 pisos|4 pisos|cuatro pisos|con sotano|con semisotano|tiene sotano", excluir="mas de cinco|mas de 5|parcial|una parte|con explosivos|dinamita")
    r("licencia_demolicion", "c", "Total mayor o con explosivos", "con explosivos|usar explosivos|usando explosivos|dinamita|implosion|mas de cinco pisos|mas de 5 pisos|seis pisos|6 pisos", excluir="sin explosivos|parcial|una parte")
    r("licencia_demolicion", "d", "Demolición parcial", "solo una parte|una parte|solo el segundo piso|un sector|algunos ambientes|unos ambientes", palabras="parcial")
    r("licencia_cerco", "a", "Cerco en lote propio", "mas de 20 metros|mas de veinte metros|mi propio lote|mi propio terreno|terreno propio|30 metros|40 metros", excluir="condominio|propiedad comun|areas comunes")
    r("licencia_cerco", "b", "Cerco en propiedad común", "junta de propietarios|propiedad comun|propiedad exclusiva y comun|areas comunes|unidades inmobiliarias", palabras="condominio")

    superior_comercial = "mas de 30000|mas de 30 000|mas de treinta mil|mas de 30 mil"
    superior_mercado = "mas de 15000|mas de 15 000|mas de quince mil|mas de 15 mil"
    superior_deportivo = "mas de 20000|mas de 20 000|mas de veinte mil|mas de 20 mil"
    comercial = "local comercial|centro de diversion|sala de espectaculos|centro cultural|cine|teatro|galeria"
    deportivo = "estadio|coliseo|local deportivo|complejo deportivo|polideportivo"
    r("licencia_edificacion_no_vivienda", "a", "Comercio hasta treinta mil metros", comercial, excluir=superior_comercial)
    r("licencia_edificacion_no_vivienda", "b", "Comercio mayor de treinta mil metros", todas=_combinaciones(comercial, superior_comercial))
    r("licencia_edificacion_no_vivienda", "c", "Mercado hasta quince mil metros", "mercado|mercado de abastos|puestos de venta", excluir=superior_mercado)
    r("licencia_edificacion_no_vivienda", "d", "Mercado mayor de quince mil metros", todas=_combinaciones("mercado|mercado de abastos", superior_mercado))
    r("licencia_edificacion_no_vivienda", "e", "Deportivo hasta veinte mil asistentes", deportivo + "|losa deportiva", excluir=superior_deportivo)
    r("licencia_edificacion_no_vivienda", "f", "Deportivo mayor de veinte mil asistentes", todas=_combinaciones(deportivo, superior_deportivo))
    r("licencia_edificacion_no_vivienda", "g", "Industria", "fabrica|planta industrial|almacen industrial|taller industrial|parque industrial", palabras="industria|industrial")
    r("licencia_edificacion_no_vivienda", "h", "Educación, salud, hospedaje o transporte", "colegio|clinica|hotel|hospedaje|grifo|terminal terrestre|universidad privada|instituto|hospital|terminal de buses")
    r("licencia_edificacion_no_vivienda", "i", "Oficinas y otros usos definidos", "oficinas|oficina|banco|iglesia|templo|almacen|deposito|taller", excluir="industrial|industria")
    r("licencia_edificacion_no_vivienda", "j", "Otras edificaciones", "no encaja en las anteriores|ninguno de los anteriores|ninguna de las anteriores|demas edificaciones|otra edificacion especial")
    r("licencia_edificacion_estado", "a", "Vivienda estatal con bono", "bono familiar habitacional|bono habitacional|programa de vivienda estatal|programa del sector vivienda|viviendas del estado")
    r("licencia_edificacion_estado", "b", "Inversión o concesión pública", "inversion publica|asociacion publico privada|concesion para servicios publicos|infraestructura publica|obra publica", excluir="vivienda|universidad|salud|colegio|comisaria")
    r("licencia_edificacion_estado", "c", "Defensa, policía o penitenciaría", "fuerzas armadas|establecimiento penitenciario|policia nacional", palabras="cuartel|comisaria|penal")
    r("licencia_edificacion_estado", "d", "Universidad nacional", "universidad nacional|universidad publica|universidad estatal")
    r("licencia_edificacion_estado", "e", "Establecimiento de salud estatal", "salud estatal|hospital publico|posta medica|centro de salud|hospital del estado")
    r("licencia_edificacion_estado", "f", "Institución educativa estatal", "colegio estatal|colegio publico|escuela publica|institucion educativa estatal|escuela del estado")

    previas = "antes de la licencia|antes de que me den la licencia|sin licencia emitida|aun no me dan la licencia|antes de obtener la licencia"
    pequenas = "cambio pequeno|cambio menor|modificacion no sustancial|cambios menores|ajuste pequeno"
    grandes = "cambio grande|cambio sustancial|modificacion sustancial|cambios grandes|modificacion importante"
    for clave, modalidad in zip("abc", "bcd"):
        r("modificacion_proyecto_edificacion", clave, f"Antes de licencia: modalidad {modalidad.upper()}", todas=_combinaciones(previas, f"modalidad {modalidad}"))
    for claves, cambios, prefijo in (("defg", pequenas, "Cambio menor"), ("hijk", grandes, "Cambio mayor")):
        for clave, modalidad in zip(claves, "abcd"):
            r("modificacion_proyecto_edificacion", clave, f"{prefijo}: modalidad {modalidad.upper()}", todas=_combinaciones(cambios, f"modalidad {modalidad}"), excluir=previas)
    for clave, modalidad in zip("abc", "bcd"):
        r("anteproyecto_consulta", clave, f"Anteproyecto modalidad {modalidad.upper()}", f"modalidad {modalidad}")
    iguales = "sin cambios|sin variaciones|igual a los planos|igual al proyecto|tal cual el plano|sin modificaciones|igualito al plano|tal cual el proyecto|igualito al proyecto"
    cambios = "con cambios|con variaciones|con modificaciones|distinto al plano|distinto al proyecto|diferente al proyecto|cambie el proyecto|modifique el proyecto"
    r("conformidad_obra", "a", "Sin cambios: modalidad A", todas=_combinaciones(iguales, "modalidad a"))
    r("conformidad_obra", "b", "Sin cambios: modalidades B, C, D", todas=_combinaciones(iguales, "modalidad b|modalidad c|modalidad d"), excluir="declaracion municipal")
    for clave, modalidad in zip("cdef", "abcd"):
        r("conformidad_obra", clave, f"Con cambios: modalidad {modalidad.upper()}", todas=_combinaciones(cambios, f"modalidad {modalidad}"), excluir="declaracion municipal")
    r("conformidad_obra", "g", "Declaración municipal de obra terminada", "declaracion municipal de edificacion terminada|declaracion municipal de obra terminada|solo la declaracion municipal")
    for claves, estado, etiqueta in (("abc", iguales, "Sin cambios"), ("def", cambios, "Con cambios")):
        for clave, modalidad in zip(claves, "bcd"):
            r("conformidad_obra_anticipada", clave, f"{etiqueta}: modalidad {modalidad.upper()}", todas=_combinaciones(estado, f"modalidad {modalidad}"))
    solo = "solo el proyecto integral|solamente el proyecto integral|unicamente el proyecto integral|solo aprobar el proyecto|sin licencia de etapa"
    juntos = "proyecto y licencia|proyecto integral y la licencia|proyecto integral con licencia|proyecto junto con la licencia|proyecto y la licencia"
    aprobado = "proyecto integral aprobado|ya aprobaron el proyecto integral|proyecto integral ya aprobado|ya tengo aprobado el proyecto|proyecto aprobado anteriormente"
    for macro in ("proyecto_integral_edificacion", "proyecto_integral_habilitacion"):
        for clave, modalidad in zip("ab", "cd"):
            r(macro, clave, f"Solo proyecto: modalidad {modalidad.upper()}", todas=_combinaciones(solo, f"modalidad {modalidad}"), excluir="modificar|modificacion")
        for clave, modalidad in zip("cd", "cd"):
            r(macro, clave, f"Proyecto y etapa: modalidad {modalidad.upper()}", todas=_combinaciones(juntos, f"modalidad {modalidad}"), excluir="modificar|modificacion")
        r(macro, "e", "Etapa de proyecto ya aprobado", aprobado, excluir="modificar|modificacion|cambiar el proyecto")
    r("proyecto_integral_edificacion", "f", "Modificar etapa aprobada: modalidad B", todas=_combinaciones("modificar|modificacion|cambiar el proyecto", "etapa|proyecto integral"))
    for clave, tramite, estado in (("a", "edificacion|construccion", "prorrogar|prorroga|todavia vigente|aun vigente"), ("b", "edificacion|construccion", "revalidar|revalidacion|ya vencio|esta vencida|licencia vencida"), ("c", "habilitacion urbana", "prorrogar|prorroga|todavia vigente|aun vigente"), ("d", "habilitacion urbana", "revalidar|revalidacion|ya vencio|esta vencida|licencia vencida")):
        r("prorroga_revalidacion_licencia", clave, ("Prorrogar" if clave in "ac" else "Revalidar") + (" edificación" if clave in "ab" else " habilitación urbana"), todas=_combinaciones(tramite, estado))
    for clave, modalidad in zip("abcd", "abcd"):
        r("modificacion_habilitacion_urbana", clave, f"Modalidad {modalidad.upper()}", f"modalidad {modalidad}")
    r("independizacion_terreno_rustico", "a", "Solo dividir en zona urbana", "solo dividir en zona urbana|dividir dentro de la zona urbana|solo independizar en zona urbana|solo dividir un terreno rustico urbano|dividir terreno rustico dentro de zona urbana", excluir="habilitar")
    r("independizacion_terreno_rustico", "b", "Solo dividir en expansión urbana", "solo dividir en expansion urbana|solo independizar en expansion|zona de expansion urbana|urbanizable inmediata", excluir="habilitar")
    for clave, modalidad in zip("cde", "bcd"):
        r("independizacion_terreno_rustico", clave, f"Dividir y habilitar: modalidad {modalidad.upper()}", todas=_combinaciones("dividir y habilitar|dividirlo y habilitarlo|independizar y habilitar", f"modalidad {modalidad}"), excluir="no colinda|no colindante|sin colindancia|no ejecutados")
    r("independizacion_terreno_rustico", "f", "Dividir y habilitar sin colindancia", "no colinda con zona urbana|no colinda con la zona urbana|sin colindancia urbana|no colindante con zona urbana|proyectos aprobados no ejecutados")
    for claves, estado, etiqueta in (("abcd", iguales, "Sin cambios"), ("efgh", cambios, "Con cambios")):
        for clave, modalidad in zip(claves, "abcd"):
            r("recepcion_obras_habilitacion", clave, f"{etiqueta}: modalidad {modalidad.upper()}", todas=_combinaciones(estado, f"modalidad {modalidad}"), excluir="parcial|solo una etapa|etapa terminada")
    r("recepcion_obras_habilitacion", "i", "Recepción parcial de etapa", "recepcion parcial|solo una etapa|etapa terminada|recibir una etapa|solo la primera etapa")
    r("regularizacion_obras", "a", "Solo habilitación sin licencia", "solo habilite|solo habilitacion|unicamente habilite|habilitacion sin construccion|solo lotes y calles", excluir="y construi|y construccion")
    r("regularizacion_obras", "b", "Habilitación y edificación sin licencia", "habilite y construi|habilitacion y construccion|terreno y construccion|habilitar y edificar|las dos cosas juntas|habilitacion y edificacion")
    r("regularizacion_obras", "c", "Solo edificación sin licencia", "solo construi|solo edifique|solo construccion|solo edificacion|solo amplie|solo remodele")
    r("libre_disponibilidad", "a", "Lote urbano privado", "mi lote urbano|lote urbano propio|soy propietario|terreno privado|lote de mi propiedad", excluir="uso publico|area publica|inversion publica")
    r("libre_disponibilidad", "b", "Área de uso público", "uso publico|area publica|terreno de aportes|vias publicas|inversion publica")
    r("obras_via_publica", "a", "Vereda o rampa frente al predio", "construir la vereda|arreglar la vereda|acondicionar la vereda|construir una rampa|reparar mi vereda", excluir="romper|abrir|conformidad|ya termine")
    r("obras_via_publica", "b", "Conformidad de obra pública terminada", "ya termine|obra terminada|conformidad de obra|obra finalizada|ya conclui")
    r("obras_via_publica", "c", "Materiales en berma", "dejar materiales|ocupar la berma|materiales de construccion|instalaciones provisionales|depositar arena")
    r("obras_via_publica", "d", "Redes de servicios públicos", "empresa de servicios|mantenimiento de redes|instalar redes|red de gas|red electrica", excluir="ya termine|conformidad")
    r("obras_via_publica", "e", "Apertura de pistas o veredas", "romper la pista|abrir la pista|apertura de pistas|romper la vereda|abrir la vereda")
    terminada = "ya termine|ya instale|instalacion terminada|conformidad de ejecucion|conformidad de instalacion"
    r("telecomunicaciones", "a", "Conformidad de instalación terminada", terminada)
    r("telecomunicaciones", "b", "Instalar redes de banda ancha", "banda ancha|fibra optica|instalar fibra|red de internet", excluir=terminada + "|ampliar el plazo|ampliacion de plazo|prorroga")
    r("telecomunicaciones", "c", "Instalar estación de radiocomunicación", "radiocomunicacion|antena|torre|estacion base|estacion de radio", excluir=terminada + "|ampliar el plazo|ampliacion de plazo|prorroga")
    r("telecomunicaciones", "d", "Otras infraestructuras de telecomunicaciones", "cableado|postes|ductos|camaras subterraneas|infraestructura distinta|otra infraestructura de telecomunicaciones", excluir="fibra|banda ancha|antena|radiocomunicacion|ya termine|conformidad|ampliar el plazo|ampliacion de plazo|prorroga")
    r("telecomunicaciones", "e", "Ampliar plazo de autorización", "ampliacion de plazo|ampliar el plazo|mas plazo|extender el plazo|prorroga")
    r("gestion_licencia", "a", "Cambiar giro", "cambio de giro|cambiar de giro|cambiar el giro|otro rubro|cambiar de rubro")
    r("gestion_licencia", "b", "Transferir o cambiar denominación", "transferencia de licencia|transferir la licencia|transferir mi licencia|cambio de denominacion|nuevo propietario|nuevo comprador|vender mi tienda|pasarle la licencia")
    r("gestion_licencia", "c", "Cese de actividades", "cese de actividades|cese definitivo|cerrar mi negocio|cierro mi negocio|dar de baja mi licencia")
    r("gestion_licencia", "d", "Duplicado de licencia", "duplicado de licencia|duplicado de mi licencia|perdi mi licencia|extravio de licencia|me robaron la licencia|otra copia de la licencia")

    # Grupos explícitos, con claves originales y alternativas disjuntas.
    def grupos(macro, especificaciones):
        config = macros["consultar_" + macro]
        config["grupos"] = {str(i): {"etiqueta": etiqueta, "opciones": list(claves), "frases": _lista(frases)}
                            for i, (etiqueta, claves, frases) in enumerate(especificaciones, 1)}

    grupos("habilitacion_urbana", [
        ("Proyecto del Estado", "ab", "proyecto del estado|proyecto estatal|proyectos estatales"),
        ("Terreno residencial pequeño", "cd", "terreno residencial pequeno|terreno residencial|residencial pequeno"),
        ("Habilitar y construir a la vez", "ef", "habilitar y construir|habilitacion y construccion|habilitar y edificar"),
        ("Casos especiales", "ghijk", "casos especiales|caso especial"),
    ])
    grupos("matrimonio_civil", [("En la municipalidad", "ac", "ceremonia municipal"), ("Fuera del local municipal", "bde", "fuera del local municipal|otro lugar"), ("Ceremonias especiales", "fg", "ceremonia especial")])
    grupos("puesto_mercado", [("Obtener o renovar", "ab", "obtener o renovar"), ("Sucesión o puesto vacante", "cd", "sucesion o vacante"), ("Modificar mi puesto", "ef", "modificar mi puesto|cambios en mi puesto")])
    grupos("itse", [("Certificado inicial", "abcd", "primera inspeccion|itse inicial|primer certificado"), ("Renovar certificado", "efgh", "renovar mi itse|renovacion de itse|itse vencido|renovar el certificado itse"), ("Duplicado", "i", "reposicion del itse")])
    grupos("licencia_ampliacion_remodelacion", [("Vivienda y obras menores", "abcd", "obra en vivienda|trabajos en mi casa"), ("Edificio comercial o multifamiliar", "e", "proyecto comercial"), ("Industria o servicios especiales", "f", "servicios especiales")])
    grupos("licencia_edificacion_no_vivienda", [("Comercio y mercados", "abcd", "comercio o mercado|proyecto comercial"), ("Deporte", "ef", "proyecto deportivo"), ("Industria y servicios", "gh", "industria o servicios"), ("Otros usos", "ij", "otros usos|otros edificios")])
    grupos("licencia_edificacion_estado", [("Vivienda e inversión pública", "ab", "vivienda o inversion"), ("Seguridad y defensa", "c", "seguridad y defensa"), ("Educación y salud", "def", "educacion y salud|servicios sociales")])
    grupos("modificacion_proyecto_edificacion", [("Antes de obtener licencia", "abc", previas), ("Cambios menores después de licencia", "defg", pequenas), ("Cambios mayores después de licencia", "hijk", grandes)])
    grupos("conformidad_obra", [("Obra sin cambios", "ab", iguales), ("Obra con cambios", "cdef", cambios), ("Solo declaración municipal", "g", "solo declaracion")])
    grupos("conformidad_obra_anticipada", [("Casco modalidad B", "ad", "modalidad b"), ("Casco modalidad C", "be", "modalidad c"), ("Casco modalidad D", "cf", "modalidad d")])
    grupos("proyecto_integral_edificacion", [("Aprobar proyecto integral", "ab", solo), ("Proyecto y licencia simultáneos", "cd", juntos), ("Proyecto ya aprobado", "ef", aprobado)])
    grupos("independizacion_terreno_rustico", [("Solo dividir", "ab", "solo dividir|solo independizar"), ("Dividir y habilitar", "cde", "dividir y habilitar|independizar y habilitar"), ("Terreno sin colindancia urbana", "f", "sin colindancia urbana|no colinda con zona urbana")])
    grupos("recepcion_obras_habilitacion", [("Obras sin cambios", "abcd", iguales), ("Obras con cambios", "efgh", cambios), ("Recepción parcial", "i", "recibir por etapas")])

    for clave, config in macros.items():
        config["pregunta"] = "¿Cuál es tu caso?"
        config.setdefault("frases_no_seguro", []).extend(["no estoy segura", "no lo se", "ni idea"])
        config["frases_no_seguro"] = list(dict.fromkeys(config["frases_no_seguro"]))
        if len(config["opciones"]) > 5 and "grupos" not in config:
            raise ValueError(f"Faltan grupos para {clave}")
        if "grupos" in config:
            claves = [k for g in config["grupos"].values() for k in g["opciones"]]
            if sorted(claves) != sorted(config["opciones"]) or len(claves) != len(set(claves)):
                raise ValueError(f"Grupos incompletos o repetidos en {clave}")
            if not 3 <= len(config["grupos"]) <= 5 or any(not 1 <= len(g["opciones"]) <= 5 for g in config["grupos"].values()):
                raise ValueError(f"El árbol debe tener dos niveles breves en {clave}")
        for opcion in config["opciones"].values():
            if not opcion.get("etiqueta") or len(opcion["etiqueta"].split()) >= 8:
                raise ValueError(f"Etiqueta de menú inválida en {clave}")

    # Formas flexionadas completas, conservando la comparación exacta.
    macros["consultar_tramite_vehicular"]["opciones"]["a"]["excluir"].extend(["razon social", "datos", "nombre"])
    macros["consultar_tramite_vehicular"]["opciones"]["b"]["frases"].extend(["esta vencida", "renovarla", "renovarlo"])
    macros["consultar_gestion_flota_vehicular"]["opciones"]["b"]["frases"].extend(["esta vencido", "renovarlo"])
    macros["consultar_divorcio"]["opciones"]["b"]["frases"].append("separacion esta aprobada")
    macros["consultar_puesto_mercado"]["opciones"]["b"]["frases"].extend(["esta por vencer", "renovarlo"])
    macros["consultar_obras_via_publica"]["opciones"]["b"]["frases"].append("obra esta terminada")
    macros["consultar_telecomunicaciones"]["opciones"]["a"]["frases"].append("instalacion esta terminada")
    macros["consultar_matrimonio_civil"]["anclas"] = ["casarme", "casarnos", "matrimonio", "boda", "casar"]
    macros["consultar_matrimonio_civil"]["opciones"]["a"]["frases"].append("casarme la municipalidad")
    # Formas ciudadanas que identifican una alternativa, sin exigir su título.
    macros['consultar_habilitacion_urbana']['opciones']['a']['palabras'].add('concesion')
    macros['consultar_habilitacion_urbana']['opciones']['b']['frases'].extend(['vivienda estatal', 'viviendas estatales'])
    macros['consultar_habilitacion_urbana']['grupos']['3']['frases'].extend([
        'construir a la vez', 'construir al mismo tiempo', 'las dos cosas a la vez',
    ])
    macros['consultar_licencia_ampliacion_remodelacion']['opciones']['e']['palabras'].add('multifamiliar')
