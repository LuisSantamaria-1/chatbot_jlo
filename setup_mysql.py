"""
setup_mysql.py
----------------
Script para conectar a MySQL/MariaDB (127.0.0.1:3306), crear la base de datos `municipal_db`,
crear las tablas y poblarlas automáticamente.
"""

import os
import sys
import pymysql

MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASS = os.environ.get("MYSQL_PASSWORD", "")
DB_NAME = os.environ.get("MYSQL_DB", "municipal_db")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SQL_FILE = os.path.join(BASE_DIR, "database_mysql.sql")

def main():
    print("==========================================================")
    print("  CONFIGURADOR E INICIALIZADOR DE BASE DE DATOS MYSQL")
    print("==========================================================")
    print(f"Conectando a MySQL en {MYSQL_HOST}:{MYSQL_PORT} (Usuario: '{MYSQL_USER}')...")

    try:
        # 1. Crear Base de Datos si no existe
        conn_init = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASS,
            autocommit=True,
            charset="utf8mb4"
        )
        with conn_init.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci;")
        conn_init.close()

        # 2. Conectar a `municipal_db` con MULTI_STATEMENTS activable
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASS,
            database=DB_NAME,
            autocommit=True,
            charset="utf8mb4",
            client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS
        )

        if os.path.exists(SQL_FILE):
            print(f"Ejecutando script de estructura y datos desde: {SQL_FILE}...")
            with open(SQL_FILE, "r", encoding="utf-8") as f:
                sql_content = f.read()

            with conn.cursor() as cur:
                cur.execute(sql_content)

            print(f"¡Base de datos '{DB_NAME}' creada y poblada correctamente en MySQL!")
        
        conn.close()

        print("\n----------------------------------------------------------")
        print("CONEXIÓN DE PYTHON / FLASK A MYSQL:")
        print(f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASS}@{MYSQL_HOST}:{MYSQL_PORT}/{DB_NAME}")
        print("----------------------------------------------------------\n")

    except Exception as e:
        print(f"\n❌ Error al configurar MySQL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
