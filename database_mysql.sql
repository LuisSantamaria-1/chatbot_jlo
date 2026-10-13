-- ===========================================================================
-- SCRIPT DE CREACIÓN Y POBLADO DE BASE DE DATOS MYSQL / MARIADB
-- Proyecto: Chatbot Municipal MDJLO (TUPA 2026)
-- Servidor: MySQL 5.7+ / MariaDB 10.2+ (Host: 127.0.0.1, Port: 3306)
-- ===========================================================================

CREATE DATABASE IF NOT EXISTS `municipal_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci;
USE `municipal_db`;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `requisitos`;
DROP TABLE IF EXISTS `tramites`;
DROP TABLE IF EXISTS `usuarios`;
DROP TABLE IF EXISTS `roles`;
SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------------
-- TABLA 1: ROLES DE SEGURIDAD
-- ---------------------------------------------------------------------------
CREATE TABLE `roles` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `nombre` VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- ---------------------------------------------------------------------------
-- TABLA 2: USUARIOS ADMINISTRATIVOS
-- ---------------------------------------------------------------------------
CREATE TABLE `usuarios` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `rol_id` INT NOT NULL,
    CONSTRAINT `fk_usuarios_roles` FOREIGN KEY (`rol_id`) REFERENCES `roles` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- ---------------------------------------------------------------------------
-- TABLA 3: TRÁMITES MUNICIPALES (TUPA MDJLO)
-- ---------------------------------------------------------------------------
CREATE TABLE `tramites` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `id_tramite` VARCHAR(20) NOT NULL UNIQUE,
    `nombre` VARCHAR(255) NOT NULL,
    `costo` VARCHAR(100) DEFAULT NULL,
    `plazo` VARCHAR(100) DEFAULT NULL,
    INDEX `idx_id_tramite` (`id_tramite`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- ---------------------------------------------------------------------------
-- TABLA 4: REQUISITOS PROCEDIMENTALES
-- ---------------------------------------------------------------------------
CREATE TABLE `requisitos` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `descripcion` TEXT NOT NULL,
    `orden` INT NOT NULL DEFAULT 0,
    `tramite_id` INT NOT NULL,
    CONSTRAINT `fk_requisitos_tramites` FOREIGN KEY (`tramite_id`) REFERENCES `tramites` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- ---------------------------------------------------------------------------
-- POBLADO DE DATOS INICIALES: ROLES Y USUARIOS
-- ---------------------------------------------------------------------------
INSERT INTO `roles` (`id`, `nombre`) VALUES (1, 'Administrador');

INSERT INTO `usuarios` (`id`, `username`, `password_hash`, `rol_id`) VALUES (1, 'admin', 'scrypt:32768:8:1$SucGwocAyTb62Nnz$ccb93b2aadc21aecb592933b9a696bc239b01464662c5a78ca936b20c89c520803d59acf09851e412e4e66319b152304ff78c587b2883b15e6207b47eea43718', 1);

-- ---------------------------------------------------------------------------
-- POBLADO DE TRÁMITES Y REQUISITOS DESDE EL TUPA OFICIAL
-- ---------------------------------------------------------------------------
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (1, 'T_001', 'Acceso a la Información Pública creada u obtenida por la entidad que se encuentre en su posesión o bajo su control', 'Copia S/0.10 - CD S/1.00', '10 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (1, 'Solicitud presentada vía formulario o documento.', 1, 1);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (2, 'Indicar número y fecha de comprobante de pago.', 2, 1);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (2, 'T_002', 'Licencia de funcionamiento para cambio de giro', 'S/ 70.80', '2 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (3, 'Declaración jurada para informar el cambio de giro.', 1, 2);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (3, 'T_003', 'Licencia provisional de funcionamiento para bodegas', 'Gratuito', '5 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (4, 'Solicitud de Licencia Provisional (Declaración Jurada).', 1, 3);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (5, 'Declaración Jurada de cumplimiento de condiciones de seguridad de la bodega.', 2, 3);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (4, 'T_004', 'Transferencia de Licencia de Funcionamiento o Cambio de Denominación', 'S/ 50.70', '2 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (6, 'Formato de declaración jurada para licencia de funcionamiento.', 1, 4);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (7, 'Copia simple del contrato de transferencia.', 2, 4);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (5, 'T_005', 'Cese de actividades', 'Gratuito', '2 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (8, 'Comunicación de cese de actividades.', 1, 5);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (6, 'T_006', 'Duplicado de licencia de funcionamiento', 'S/ 42.90', '5 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (9, 'Solicitud simple o formato FUT.', 1, 6);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (10, 'DJ de representación o Carta Poder.', 2, 6);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (11, 'Copia simple de denuncia policial por pérdida o robo.', 3, 6);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (12, 'Pago por derecho de trámite.', 4, 6);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (7, 'T_007', 'Autorización de instalación de publicidad exterior: anuncio publicitario simple adosado', 'S/ 212.30', '15 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (13, 'Solicitud simple o según formato FUT de Publicidad Exterior.', 1, 7);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (14, 'Foto y/o fotomontaje.', 2, 7);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (15, 'Diseño de anuncio.', 3, 7);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (16, 'Pago por derecho de trámite.', 4, 7);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (8, 'T_008', 'VISACIÓN DE PLANOS PARA TRÁMITES DE PRESCRIPCIÓN ADQUISITIVA O TÍTULO SUPLETORIO Y PARA RECTIFICACIÓN Y/O DELIMITACIÓN DE ÁREAS Y LINDEROS', 'S/ 100.30', '10 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (17, 'Solicitud simple o según el formato FUT debidamente llenado.', 1, 8);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (18, 'Copia simple del documento que acredite la propiedad o posesión del predio.', 2, 8);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (19, 'Tres juegos de plano de ubicación, localización, perimétrico, lotización (con sección de vías) o manzaneo de las memorias descriptivas firmados por el profesional y el posesionario en el formato XIV - MVCS.', 3, 8);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (20, 'Pago por derecho de trámite.', 4, 8);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (21, 'Certificado de búsqueda catastral, de corresponder.', 5, 8);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (9, 'T_009', 'Divorcio Por mutuo acuerdo o separación convencional', 'S/ 313.60', '15 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (22, 'Formato de solicitud de separación convencional y divorcio ulterior.', 1, 9);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (23, 'Acta de matrimonio Actualizada (vigencia de 3 meses).', 2, 9);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (24, 'Exhibición de los DNIs de los cónyuges.', 3, 9);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (25, 'Partidas de nacimientos vigentes en los casos de tener hijos menores o DDJJ de no tener hijos menores de edad o mayores con discapacidad.', 4, 9);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (26, 'Copia certificada de la sentencia y resolución que la declara consentida o acta de conciliación extrajudicial en la que establecen tenencia alimentos y régimen de visitas a favor de los hijos menores de edad.', 5, 9);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (27, 'Testimonio de escritura pública de sustitución de sociedad de gananciales por la de separación de bienes inscrita en registros públicos o declaración jurada de no tener bienes en común.', 6, 9);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (28, 'DDJJ del último domicilio conyugal.', 7, 9);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (29, 'Pago por derecho de trámite.', 8, 9);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (10, 'T_010', 'PERMISO DE OPERACIÓN PARA PRESTAR EL SERVICIO DE TRANSPORTE PÚBLICO ESPECIAL DE PASAJEROS Y DE CARGA EN VEHÍCULOS MENORES', 'S/ 1064.40', '30 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (30, 'Solicitud simple indicando número del DNI.', 1, 10);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (31, 'Copia simple de la escritura pública de constitución de la persona jurídica inscrita en Registros Públicos.', 2, 10);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (32, 'Copia literal vigente de la partida registral.', 3, 10);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (33, 'Certificado de Vigencia de Poder de la persona natural que representa a la persona jurídica.', 4, 10);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (34, 'Exhibir el Documento Nacional de Identidad del representante legal.', 5, 10);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (35, 'Pago por derecho de tramitación.', 6, 10);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (36, 'Padrón Actualizado de Socios Propietarios y Unidades Vehiculares.', 7, 10);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (11, 'T_011', 'TARJETA DE OPERATIVIDAD DE VEHICULO Y RENOVACIÓN (vigencia 6 años renovable aplicado a vehículos formalizados)', 'S/ 66.70', '5 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (37, 'Solicitud simple.', 1, 11);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (38, 'Exhibir el numero de documento de identidad.', 2, 11);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (39, 'Copia legible de Licencia de Conducir.', 3, 11);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (40, 'Copia de Tarjeta de Propiedad o contrato de compra venta.', 4, 11);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (41, 'Copia legible del SOAT o AFOCAT vigente.', 5, 11);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (42, 'Copia legible de Ticket Libre de infracciones vigente.', 6, 11);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (43, 'Conformidad Constatación de Características del vehículo.', 7, 11);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (44, 'Copia de carnet del curso de seguridad vial vigente.', 8, 11);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (45, 'Pago por derecho de tramitación.', 9, 11);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (46, 'Boleta Informativa Expedida por la SUNARP.', 10, 11);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (47, 'Constancia de ser socio expedida por el presidente de la asociación.', 11, 11);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (48, 'Copia simple del certificado de inspección vehicular (CARTICAT).', 12, 11);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (49, 'Declaración jurada de socio.', 13, 11);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (50, 'Numero de resolución del permiso de operatividad de la asociación.', 14, 11);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (51, 'Copia del padrón de asociación.', 15, 11);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (12, 'T_012', 'BAJA Y SUSTITUCIÓN DE VEHICULO MENOR', 'S/ 59.40', '5 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (52, 'Solicitud simple.', 1, 12);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (53, 'Constancia de autorizacion de la unidad a sustituir otorgada por el presidente de la asociación o persona juridica.', 2, 12);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (54, 'Constancia de autorizacion de la baja otorgada por el presidente de la asociación o persona juridica.', 3, 12);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (55, 'Pago por derecho de tramitación.', 4, 12);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (56, 'Devolución de la tarjeta de operatividad del vehículo dada de alta.', 5, 12);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (57, 'Numero de resolucion del permiso de autorizacion.', 6, 12);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (58, 'Copia de la tarjeta de propiedad del vehiculo a efectos de la sustitución.', 7, 12);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (59, 'Exhibir el numero de documento de identidad del propietario.', 8, 12);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (60, 'Indicar N° de Resolución del permiso de operatividad.', 9, 12);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (61, 'Copia simple del padron modificado.', 10, 12);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (62, 'Constancia de ser socio consignado.', 11, 12);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (13, 'T_013', 'Registro de Organizaciones Sociales', 'Gratuito', '15 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (63, 'Solicitud Simple o en formato FUT debidamente llenada por el administrado.', 1, 13);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (64, 'Acta de Fundación o de constitución.', 2, 13);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (65, 'Norma de Organización (reglamento Estatutos u otros) y su acta de aprobación.', 3, 13);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (66, 'Padrón de miembros de la organización social.', 4, 13);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (67, 'Nómina de los miembros del órgano directivo.', 5, 13);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (68, 'Acta de elección del órgano directivo.', 6, 13);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (69, 'Copia legible del documento de identidad de los integrantes del órgano directivo.', 7, 13);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (70, 'Otros documentos de ser el caso.', 8, 13);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (14, 'T_014', 'CONDUCCIÓN DE PUESTO DE VENTA EN MERCADOS MUNICIPALES', 'Variable (desde S/ 137.50 hasta S/ 2191.70 según calificación)', '1 día hábil');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (71, 'Solicitud simple indicando número del DNI.', 1, 14);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (72, 'Ficha Empadronamiento.', 2, 14);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (73, 'Declaración Jurada de NO conducir más de 02 puestos.', 3, 14);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (74, 'Comprobante de Pago por costo administrativo.', 4, 14);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (75, 'Numero o Serie de Carnet de Comerciante emitido por la MDJLO.', 5, 14);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (15, 'T_015', 'Certificado de Numeración Municipal', 'S/ 90.30', '0 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (76, 'Solicitud simple indicando los ingresos al predio y/o las unidades inmobiliarias de las que requiere el certificado señalando el número de recibo y la fecha del pago efectuado por el derecho de tramitación.', 1, 15);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (16, 'T_016', 'Matrimonio civil (dentro del horario de trabajo en local municipal)', 'S/ 240.00', '20 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (77, 'Formato de solicitud de matrimonio civil.', 1, 16);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (78, 'Exhibir DNI de contrayentes y testigos mayores de edad.', 2, 16);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (79, 'Certificado de soltería expedido por RENIEC.', 3, 16);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (80, 'Certificado de análisis clínicos.', 4, 16);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (81, 'Publicación del Edicto Matrimonial.', 5, 16);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (82, 'Requisitos específicos para divorciados viudos o extranjeros según corresponda.', 6, 16);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (83, 'Pago por derecho de trámite.', 7, 16);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (17, 'T_017', 'Matrimonio civil (en local público dentro de la jurisdicción)', 'S/ 300.20', '20 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (84, 'Formato de solicitud de matrimonio civil.', 1, 17);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (85, 'DNI de los contrayentes y testigos mayores de edad.', 2, 17);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (86, 'Certificado de soltería expedido por RENIEC (solteros), o partida de matrimonio con divorcio registrado (divorciados), o partida de matrimonio anterior y partida de defunción (viudos), según corresponda.', 3, 17);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (87, 'Certificado de análisis clínicos.', 4, 17);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (88, 'Publicación del Edicto Matrimonial.', 5, 17);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (89, 'Para extranjeros: partida de nacimiento y certificado de soltería apostillados, copia legalizada de pasaporte y traducción visada.', 6, 17);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (90, 'Pago por derecho de trámite.', 7, 17);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (18, 'T_018', 'Matrimonio civil (fuera del horario de trabajo en local municipal)', 'S/ 266.70', '20 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (91, 'Formato de solicitud de matrimonio civil.', 1, 18);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (92, 'DNI de los contrayentes y testigos mayores de edad.', 2, 18);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (93, 'Certificado de soltería expedido por RENIEC (solteros), o partida de matrimonio con divorcio registrado (divorciados), o partida de matrimonio anterior y partida de defunción (viudos), según corresponda.', 3, 18);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (94, 'Certificado de análisis clínicos.', 4, 18);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (95, 'Publicación del Edicto Matrimonial.', 5, 18);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (96, 'Para extranjeros: partida de nacimiento y certificado de soltería apostillados, copia legalizada de pasaporte y traducción visada.', 6, 18);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (97, 'Pago por derecho de trámite.', 7, 18);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (19, 'T_019', 'Matrimonio civil (en local público fuera de la jurisdicción)', 'S/ 344.90', '20 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (98, 'Formato de solicitud de matrimonio civil.', 1, 19);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (99, 'DNI de los contrayentes y testigos mayores de edad.', 2, 19);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (100, 'Certificado de soltería expedido por RENIEC (solteros), o partida de matrimonio con divorcio registrado (divorciados), o partida de matrimonio anterior y partida de defunción (viudos), según corresponda.', 3, 19);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (101, 'Certificado de análisis clínicos.', 4, 19);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (102, 'Publicación del Edicto Matrimonial.', 5, 19);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (103, 'Para extranjeros: partida de nacimiento y certificado de soltería apostillados, copia legalizada de pasaporte y traducción visada.', 6, 19);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (104, 'Pago por derecho de trámite.', 7, 19);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (20, 'T_020', 'Matrimonio civil (a domicilio dentro de la jurisdicción)', 'S/ 290.10', '20 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (105, 'Formato de solicitud de matrimonio civil.', 1, 20);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (106, 'DNI de los contrayentes y testigos mayores de edad.', 2, 20);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (107, 'Certificado de soltería expedido por RENIEC (solteros), o partida de matrimonio con divorcio registrado (divorciados), o partida de matrimonio anterior y partida de defunción (viudos), según corresponda.', 3, 20);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (108, 'Certificado de análisis clínicos.', 4, 20);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (109, 'Publicación del Edicto Matrimonial.', 5, 20);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (110, 'Para extranjeros: partida de nacimiento y certificado de soltería apostillados, copia legalizada de pasaporte y traducción visada.', 6, 20);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (111, 'Pago por derecho de trámite.', 7, 20);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (21, 'T_021', 'Matrimonio civil (ceremonia oficiada por el Alcalde)', 'S/ 390.10', '20 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (112, 'Formato de solicitud de matrimonio civil.', 1, 21);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (113, 'DNI de los contrayentes y testigos mayores de edad.', 2, 21);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (114, 'Certificado de soltería expedido por RENIEC (solteros), o partida de matrimonio con divorcio registrado (divorciados), o partida de matrimonio anterior y partida de defunción (viudos), según corresponda.', 3, 21);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (115, 'Certificado de análisis clínicos.', 4, 21);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (116, 'Publicación del Edicto Matrimonial.', 5, 21);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (117, 'Para extranjeros: partida de nacimiento y certificado de soltería apostillados, copia legalizada de pasaporte y traducción visada.', 6, 21);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (118, 'Pago por derecho de trámite.', 7, 21);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (22, 'T_022', 'Matrimonio civil comunitario', 'S/ 100.10', '20 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (119, 'Formato de solicitud de matrimonio civil.', 1, 22);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (120, 'DNI de los contrayentes y testigos mayores de edad.', 2, 22);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (121, 'Certificado de soltería expedido por RENIEC (solteros), o partida de matrimonio con divorcio registrado (divorciados), o partida de matrimonio anterior y partida de defunción (viudos), según corresponda.', 3, 22);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (122, 'Certificado de análisis clínicos.', 4, 22);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (123, 'Publicación del Edicto Matrimonial.', 5, 22);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (124, 'Para extranjeros: partida de nacimiento y certificado de soltería apostillados, copia legalizada de pasaporte y traducción visada.', 6, 22);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (125, 'Pago por derecho de trámite.', 7, 22);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (23, 'T_023', 'Inscripción en registro canino municipal', 'S/ 20.10', '7 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (126, 'Solicitud en formato FUT debidamente llenada por el administrado (donde conste las características del can que permitan su plena identificación).', 1, 23);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (127, 'Presentar Carnet de Vacunación completa (Validado por el colegio Médico Veterinario o un profesional Médico veterinario colegiado y habilitado).', 2, 23);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (128, 'Copia del recibo de luz o agua del tenedor o propietario del can.', 3, 23);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (129, 'Foto tamaño pasaporte del can.', 4, 23);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (130, 'Pago por derecho de trámite.', 5, 23);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (24, 'T_024', 'Inscripción en Registro Canino Municipal de Canes Potencialmente Peligrosos', 'S/ 20.00', '7 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (131, 'Solicitud en formato FUT con características que identifiquen plenamente al can.', 1, 24);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (132, 'Carnet de vacunación completo, validado por médico veterinario colegiado.', 2, 24);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (133, 'Certificado o constancia de aptitud psicológica del dueño, expedido por psicólogo colegiado.', 3, 24);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (134, 'Copia del recibo de luz o agua del tenedor o propietario.', 4, 24);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (135, 'Pago por derecho de trámite.', 5, 24);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (136, 'Nota: el propietario debe ser mayor de edad y presentar certificado de vacunación antirrábica y desparasitación.', 6, 24);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (25, 'T_025', 'Autorización para instalación de conexiones domiciliarias de agua y desagüe (persona natural)', 'S/ 169.80', '10 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (137, 'Formulario único de trámite (FUT), debidamente llenado.', 1, 25);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (138, 'Documentación que acredite derecho a realizar trabajos (si no es propietario).', 2, 25);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (139, 'Copia simple de carta de EPSEL SA autorizando trabajos.', 3, 25);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (140, 'Declaración Jurada de compromiso de reposición de infraestructura pública.', 4, 25);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (141, 'Pago por derecho de trámite.', 5, 25);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (26, 'T_026', 'Autorización para instalación de conexiones domiciliarias de agua y desagüe (persona jurídica)', 'S/ 249.70', '10 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (142, 'Formulario único de trámite (FUT).', 1, 26);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (143, 'Documento que acredite la representación legal.', 2, 26);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (144, 'Copia de proyecto aprobado por la entidad correspondiente.', 3, 26);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (145, 'Declaración jurada de responsabilidad de obra.', 4, 26);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (146, 'Declaración jurada de habilidad del profesional responsable del proyecto.', 5, 26);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (147, 'Pago por derecho de trámite.', 6, 26);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (27, 'T_027', 'Certificado de Compatibilidad de Uso', 'S/ 90.70', '10 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (148, 'Solicitud simple o FUT (indicando RUC y giro de negocio).', 1, 27);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (149, 'Croquis o plano de ubicación (si corresponde).', 2, 27);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (150, 'Pago por derecho de trámite.', 3, 27);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (28, 'T_028', 'Certificación sanitaria municipal para establecimientos comerciales y de servicios', 'S/ 80.10', '5 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (151, 'Solicitud simple o FUT (indicando N° Licencia de Funcionamiento o ITSE).', 1, 28);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (152, 'Exhibir DNI.', 2, 28);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (153, 'Carta poder simple (si es representante legal).', 3, 28);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (154, 'Copia de certificado de fumigación vigente.', 4, 28);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (155, 'Copia de autorización o resolución sectorial (si corresponde).', 5, 28);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (156, 'Pago por derecho de trámite.', 6, 28);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (29, 'T_029', 'Recurso de Reconsideración', 'Gratuito', '15 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (157, 'Escrito fundamentado y firmado por el interesado o representante legal.', 1, 29);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (158, 'Consignar N° de DNI y N° de Resolución emitida por la MDJLO de la cual solicita reconsideración (debe sustentarse en nueva prueba).', 2, 29);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (30, 'T_030', 'Autorización Temporal para el Desarrollo de Espectáculos Públicos No Deportivos', 'S/ 245.80', '10 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (159, 'Solicitud simple o FUT indicando detalles del evento (tipo, fecha, hora, área, medidas de seguridad).', 1, 30);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (160, 'Indicar el número de Resolución de Evaluación de Condiciones de Seguridad del evento.', 2, 30);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (161, 'Copia simple del contrato de alquiler o cesión de uso del local.', 3, 30);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (162, 'Copia de la autorización de APDAYC (de ser el caso).', 4, 30);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (163, 'Copia simple del contrato entre el promotor y los artistas (de corresponder).', 5, 30);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (164, 'Copia simple de la solicitud ante la gobernación José Leonardo Ortiz.', 6, 30);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (165, 'Contar con licencia de funcionamiento (de ser el caso).', 7, 30);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (166, 'Pago de importe por impuesto a los espectáculos públicos no deportivos.', 8, 30);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (167, 'Copia simple del contrato de seguridad con la empresa prestadora.', 9, 30);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (168, 'Copia simple del pago efectuado ante la prefectura por garantía.', 10, 30);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (169, 'Pago por derecho de trámite. (Presentar con un mínimo de 10 días de anticipación).', 11, 30);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (31, 'T_031', 'Certificado de Posesión para la Factibilidad de Servicios Básicos', 'S/ 80.00', '10 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (170, 'Solicitud simple o formato llenado (indicando DNI, correo electrónico, celular).', 1, 31);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (171, 'Croquis de ubicación.', 2, 31);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (172, 'Acta de colindancia debidamente llenada según formato.', 3, 31);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (173, 'Copias simples de documentos que acrediten propiedad y/o DDJJ de posesión de vivienda.', 4, 31);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (174, 'Pago por derecho de trámite.', 5, 31);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (32, 'T_032', 'Constancia de Inhabitabilidad y Estado Ruinoso', 'S/ 68.80', '5 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (175, 'Solicitud en formato FUT, debidamente llenada.', 1, 32);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (176, 'Plano y/o croquis de ubicación del inmueble.', 2, 32);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (177, 'Pago por derecho de trámite.', 3, 32);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (33, 'T_033', 'Certificado de Parámetros Urbanísticos y Edificatorios', 'S/ 106.50', '5 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (178, 'Solicitud simple o FUT, debidamente llenado.', 1, 33);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (179, 'Copia simple del documento que acredite la propiedad.', 2, 33);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (180, 'Plano de ubicación y localización (con sección de vías), según formato XIV - MVCS.', 3, 33);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (181, 'Pago por derecho de trámite. (Documentación técnica firmada por el propietario y profesional competente/habilitado).', 4, 33);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (34, 'T_034', 'Divorcio Ulterior', 'S/ 200.10', '15 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (182, 'Formato de Solicitud de Divorcio Ulterior dirigida al Alcalde, indicando N° y fecha de resolución que declaró la separación convencional.', 1, 34);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (183, 'Exhibir DNIs de ambos cónyuges.', 2, 34);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (184, 'Pago por derecho de trámite.', 3, 34);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (185, 'Nota: solo procede tras 2 meses de emitida la separación convencional.', 4, 34);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (35, 'T_045', 'Registro y/o Empadronamiento Municipal de Vehículos Menores del Servicio Especial de Pasajeros y de Carga', 'S/ 269.90', '25 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (186, 'Solicitud simple o formato FUT debidamente llenado.', 1, 35);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (187, 'Boleta Informativa de Registros Públicos (no mayor a 30 días).', 2, 35);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (188, 'Copia simple de la Tarjeta de Propiedad Vehicular.', 3, 35);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (189, 'Pago por derecho de trámite.', 4, 35);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (36, 'T_046', 'Autorización Anual para Uso de Paradero o para Vehículos Menores del Servicio Especial', 'S/ 259.60', '5 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (190, 'Solicitud simple según formato FUT.', 1, 36);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (191, 'Certificado de Vigencia de Poder del representante (antigüedad no mayor a 15 días).', 2, 36);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (192, 'Documento de identidad del presidente de la asociación.', 3, 36);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (193, 'Número de resolución del permiso de operatividad.', 4, 36);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (194, 'Pago por derecho de trámite.', 5, 36);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (37, 'T_047', 'Incremento de Flota Vehicular (Vehículos Menores)', 'S/ 180.20', '10 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (195, 'Solicitud simple o Formato FUT.', 1, 37);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (196, 'DNI del presidente de la asociación y del propietario del vehículo.', 2, 37);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (197, 'Número de resolución del permiso de operatividad.', 3, 37);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (198, 'Conformidad de constatación de características del nuevo vehículo o recibo de pago.', 4, 37);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (199, 'Copia simple de tarjeta de propiedad vigente.', 5, 37);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (200, 'Copia simple de licencia de conducir vigente.', 6, 37);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (201, 'Copia del SOAT o FORCAT vigentes.', 7, 37);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (202, 'Boucher de pago de la tarjeta de operatividad.', 8, 37);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (203, 'Carnet vial o Boucher de pago.', 9, 37);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (204, 'Pago por derecho de trámite.', 10, 37);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (38, 'T_048', 'Renovación de Permiso de Operación para Transporte Público Especial de Pasajeros y Carga en Vehículos Menores (Vigencia 10 años)', 'S/ 1213.10', '30 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (205, 'Solicitud o FUT con carácter de declaración jurada (datos de persona jurídica, lista de prestadores, vehículos y modificaciones).', 1, 38);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (206, 'Copia simple del contrato de alquiler del vehículo (si el prestador no es propietario).', 2, 38);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (207, 'Constancia y fecha de pago por derecho de trámite.', 3, 38);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (39, 'T_049', 'Duplicado de Tarjeta de Operatividad de Vehículos Menores', 'S/ 30.50', '5 días hábiles');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (208, 'Solicitud simple o Formato FUT.', 1, 39);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (209, 'Exhibir DNI.', 2, 39);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (210, 'Pago por derecho de trámite.', 3, 39);
INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES (40, 'T_080', 'Licencia de Edificación Modalidad A', 'S/ 150.00', 'Aprobación Automática');
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (211, 'Formulario Único de Edificación (FUE) debidamente suscrito.', 1, 40);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (212, 'Documento que acredite el derecho a edificar.', 2, 40);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (213, 'Declaración Jurada de los profesionales responsables.', 3, 40);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (214, 'Planos de ubicación y arquitectura.', 4, 40);
INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES (215, 'Comprobante de pago por derecho de trámite.', 5, 40);
