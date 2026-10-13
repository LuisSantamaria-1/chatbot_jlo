import csv
import re
import sys
import os

sys.path.insert(0, os.getcwd())
from app import app
from backend.models import db, Tramite, Requisito

csv_path = 'data/tramites.csv'
csv_data = {}
with open(csv_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        tid = (row.get('ID_Tramite') or row.get('id_tramite') or '').strip()
        nombre = (row.get('Nombre') or row.get('nombre') or '').strip()
        costo = (row.get('Costo') or row.get('costo') or '').strip()
        plazo = (row.get('Plazo') or row.get('plazo') or '').strip()
        reqs_raw = row.get('Requisitos') or row.get('requisitos') or ''
        reqs = [r.strip() for r in reqs_raw.split('|') if r.strip()]
        csv_data[tid] = {
            'id_tramite': tid,
            'nombre': nombre,
            'costo': costo,
            'plazo': plazo,
            'requisitos': reqs
        }

db_data = {}
with app.app_context():
    for t in Tramite.query.all():
        reqs = [r.descripcion.strip() for r in t.requisitos]
        db_data[t.id_tramite.strip()] = {
            'id_tramite': t.id_tramite.strip(),
            'nombre': t.nombre.strip(),
            'costo': (t.costo or '').strip(),
            'plazo': (t.plazo or '').strip(),
            'requisitos': reqs
        }

print(f"Total trámites en CSV: {len(csv_data)}")
print(f"Total trámites en BD:  {len(db_data)}")

anomalias = {
    'codigo_fuera_formato': [],
    'costo_vacio_o_no_especificado': [],
    'costo_formato_no_uniforme': [],
    'plazo_vacio_o_no_especificado': [],
    'plazo_empieza_por_cero': [],
    'plazo_formato_no_uniforme': [],
    'tramite_sin_requisitos': [],
    'requisito_menor_15_caracteres': [],
    'requisito_cortado': [],
    'requisito_numeracion_residual': [],
    'requisito_duplicado': [],
    'diferencias_csv_vs_bd': []
}

for tid, row in csv_data.items():
    # 1. Código
    if not re.match(r'^T_\d{3}$', tid):
        anomalias['codigo_fuera_formato'].append(tid)

    # 2. Costo
    costo = row['costo']
    if not costo or costo.lower() in ('no especificado', 'ninguno', 'null', 'none'):
        anomalias['costo_vacio_o_no_especificado'].append(tid)
    elif costo != 'Gratuito' and not re.match(r'^S/\s*\d+(\.\d{2})?$', costo):
        anomalias['costo_formato_no_uniforme'].append((tid, costo))

    # 3. Plazo
    plazo = row['plazo']
    if not plazo or plazo.lower() in ('no especificado', 'ninguno', 'null', 'none'):
        anomalias['plazo_vacio_o_no_especificado'].append(tid)
    elif plazo.startswith('0'):
        anomalias['plazo_empieza_por_cero'].append((tid, plazo))
    elif not re.match(r'^\d+\s+días\s+hábiles$', plazo) and plazo != 'Inmediato':
        anomalias['plazo_formato_no_uniforme'].append((tid, plazo))

    # 4. Requisitos
    reqs = row['requisitos']
    if len(reqs) == 0:
        anomalias['tramite_sin_requisitos'].append(tid)

    if len(reqs) != len(set(reqs)):
        anomalias['requisito_duplicado'].append(tid)

    for r in reqs:
        if len(r) < 15:
            anomalias['requisito_menor_15_caracteres'].append((tid, r))
        if r.endswith('...') or r.endswith('..') or re.search(r'[a-zA-Z]+-$', r):
            anomalias['requisito_cortado'].append((tid, r))
        if re.match(r'^(\d+[\.\-\)]|[a-zA-Z][\.\-\)])\s*', r):
            anomalias['requisito_numeracion_residual'].append((tid, r))

    # 5. Comparación con BD
    if tid not in db_data:
        anomalias['diferencias_csv_vs_bd'].append((tid, 'No existe en BD'))
    else:
        db_row = db_data[tid]
        diffs = []
        if row['nombre'] != db_row['nombre']:
            diffs.append('nombre')
        if row['costo'] != db_row['costo']:
            diffs.append(f"costo (csv:'{row['costo']}' vs bd:'{db_row['costo']}')")
        if row['plazo'] != db_row['plazo']:
            diffs.append(f"plazo (csv:'{row['plazo']}' vs bd:'{db_row['plazo']}')")
        if row['requisitos'] != db_row['requisitos']:
            diffs.append(f"requisitos (csv:{len(row['requisitos'])} vs bd:{len(db_row['requisitos'])})")
        if diffs:
            anomalias['diferencias_csv_vs_bd'].append((tid, diffs))

print('\n' + '=' * 60)
print('         DETALLE DE ANOMALÍAS EN TRAMITES')
print('=' * 60)
for k, v in anomalias.items():
    print(f"\n[{k}] - Total: {len(v)}")
    for item in v:
        print(f"   -> {item}")
