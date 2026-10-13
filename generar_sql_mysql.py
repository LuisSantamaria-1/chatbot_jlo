"""
generar_sql_mysql.py
---------------------
Genera el archivo script 'database_mysql.sql' completo con tablas y datos del TUPA.
"""
import csv
import os
import secrets
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CSV_PATH = os.path.join(BASE_DIR, "tramites.csv")
SQL_OUTPUT = os.path.join(BASE_DIR, "database_mysql.sql")

lines = [
    "-- ===========================================================================",
    "-- SCRIPT DE CREACIÓN Y POBLADO DE BASE DE DATOS MYSQL / MARIADB",
    "-- Proyecto: Chatbot Municipal MDJLO (TUPA 2026)",
    "-- Servidor: MySQL 5.7+ / MariaDB 10.2+ (Host: 127.0.0.1, Port: 3306)",
    "-- ===========================================================================",
    "",
    "CREATE DATABASE IF NOT EXISTS `municipal_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci;",
    "USE `municipal_db`;",
    "",
    "SET FOREIGN_KEY_CHECKS = 0;",
    "DROP TABLE IF EXISTS `requisitos`;",
    "DROP TABLE IF EXISTS `tramites`;",
    "DROP TABLE IF EXISTS `usuarios`;",
    "DROP TABLE IF EXISTS `roles`;",
    "SET FOREIGN_KEY_CHECKS = 1;",
    "",
    "-- ---------------------------------------------------------------------------",
    "-- TABLA 1: ROLES DE SEGURIDAD",
    "-- ---------------------------------------------------------------------------",
    "CREATE TABLE `roles` (",
    "    `id` INT AUTO_INCREMENT PRIMARY KEY,",
    "    `nombre` VARCHAR(50) NOT NULL UNIQUE",
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;",
    "",
    "-- ---------------------------------------------------------------------------",
    "-- TABLA 2: USUARIOS ADMINISTRATIVOS",
    "-- ---------------------------------------------------------------------------",
    "CREATE TABLE `usuarios` (",
    "    `id` INT AUTO_INCREMENT PRIMARY KEY,",
    "    `username` VARCHAR(50) NOT NULL UNIQUE,",
    "    `password_hash` VARCHAR(255) NOT NULL,",
    "    `rol_id` INT NOT NULL,",
    "    CONSTRAINT `fk_usuarios_roles` FOREIGN KEY (`rol_id`) REFERENCES `roles` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE",
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;",
    "",
    "-- ---------------------------------------------------------------------------",
    "-- TABLA 3: TRÁMITES MUNICIPALES (TUPA MDJLO)",
    "-- ---------------------------------------------------------------------------",
    "CREATE TABLE `tramites` (",
    "    `id` INT AUTO_INCREMENT PRIMARY KEY,",
    "    `id_tramite` VARCHAR(20) NOT NULL UNIQUE,",
    "    `nombre` VARCHAR(255) NOT NULL,",
    "    `costo` VARCHAR(100) DEFAULT NULL,",
    "    `plazo` VARCHAR(100) DEFAULT NULL,",
    "    INDEX `idx_id_tramite` (`id_tramite`)",
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;",
    "",
    "-- ---------------------------------------------------------------------------",
    "-- TABLA 4: REQUISITOS PROCEDIMENTALES",
    "-- ---------------------------------------------------------------------------",
    "CREATE TABLE `requisitos` (",
    "    `id` INT AUTO_INCREMENT PRIMARY KEY,",
    "    `descripcion` TEXT NOT NULL,",
    "    `orden` INT NOT NULL DEFAULT 0,",
    "    `tramite_id` INT NOT NULL,",
    "    CONSTRAINT `fk_requisitos_tramites` FOREIGN KEY (`tramite_id`) REFERENCES `tramites` (`id`) ON DELETE CASCADE ON UPDATE CASCADE",
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;",
    "",
    "-- ---------------------------------------------------------------------------",
    "-- POBLADO DE DATOS INICIALES: ROLES Y USUARIOS",
    "-- ---------------------------------------------------------------------------",
    "INSERT INTO `roles` (`id`, `nombre`) VALUES (1, 'Administrador');",
    "",
]

# Generar hash de contraseña inicial segura
pwd_inicial = os.environ.get("ADMIN_INITIAL_PASSWORD") or os.environ.get("ADMIN_PASSWORD") or secrets.token_urlsafe(12)
hash_admin = generate_password_hash(pwd_inicial)

lines.append(f"INSERT INTO `usuarios` (`id`, `username`, `password_hash`, `rol_id`) VALUES (1, 'admin', '{hash_admin}', 1);")
lines.append("")

lines.append("-- ---------------------------------------------------------------------------")
lines.append("-- POBLADO DE TRÁMITES Y REQUISITOS DESDE EL TUPA OFICIAL")
lines.append("-- ---------------------------------------------------------------------------")

def _limpiar(txt):
    txt = txt.strip()
    partes = txt.split(". ", 1)
    if len(partes) == 2 and partes[0].strip().isdigit():
        return partes[1].strip()
    return txt

def _escape(val):
    val = str(val).replace("\\", "\\\\").replace("'", "''")
    return f"'{val}'"

tramite_id_counter = 1
requisito_id_counter = 1

if os.path.exists(CSV_PATH):
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            id_t = row["ID_Tramite"].strip()
            nom = row["Nombre"].strip()
            reqs_raw = row["Requisitos"].strip()
            costo = row["Costo"].strip()
            plazo = row["Plazo"].strip()

            lines.append(f"INSERT INTO `tramites` (`id`, `id_tramite`, `nombre`, `costo`, `plazo`) VALUES ({tramite_id_counter}, {_escape(id_t)}, {_escape(nom)}, {_escape(costo)}, {_escape(plazo)});")

            lista_reqs = [r.strip() for r in reqs_raw.split("|") if r.strip()]
            for orden, req_txt in enumerate(lista_reqs, start=1):
                clean_req = _limpiar(req_txt)
                lines.append(f"INSERT INTO `requisitos` (`id`, `descripcion`, `orden`, `tramite_id`) VALUES ({requisito_id_counter}, {_escape(clean_req)}, {orden}, {tramite_id_counter});")
                requisito_id_counter += 1

            tramite_id_counter += 1

with open(SQL_OUTPUT, "w", encoding="utf-8") as out:
    out.write("\n".join(lines) + "\n")

print(f"Script SQL generado con éxito en: {SQL_OUTPUT}")
