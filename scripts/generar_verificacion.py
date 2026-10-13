import csv
import re
import os

indice_path = '../Texto_INDIICE_DEL_TUPAC.txt'
indice_entries = []
if os.path.exists(indice_path):
    with open(indice_path, encoding='utf-8') as f:
        curr_num = ''
        for line in f:
            l = line.strip()
            if re.match(r'^N[°º]\s*\d+', l):
                curr_num = l
            elif l and curr_num:
                # filtrar encabezados de seccion
                if not re.match(r'^\d+\.\d+', l) and not l.startswith('SECCIÓN'):
                    indice_entries.append((curr_num, l))

# Cargar CSV actual
csv_path = 'data/tramites.csv'
with open(csv_path, encoding='utf-8') as f:
    tramites = list(csv.DictReader(f))

# Reglas de marcado para auditoría manual
# Criterios: anomalía en costo (no estándar / gratuito), plazo (0 días / no estándar), o conflicto con BD
tramites_marcados = {
    'T_001': 'Costo desglosado múltiple y desplazamiento de columnas en base de datos',
    'T_003': 'Costo declarado como Gratuito (verificar gratuidad en TUPA)',
    'T_005': 'Costo declarado como Gratuito (verificar gratuidad en TUPA)',
    'T_013': 'Costo declarado como Gratuito (verificar gratuidad en TUPA)',
    'T_014': 'Costo variable con rango descriptivo y plazo 1 días hábiles con discordancia',
    'T_015': 'Plazo registrado como 0 días hábiles (aprobación automática/inmediato)',
    'T_029': 'Costo declarado como Gratuito (verificar gratuidad en TUPA)',
    'T_080': 'Plazo registrado como Aprobación Automática (verificar plazo en TUPA)',
}

def normalizar(s):
    s = s.lower()
    for a, b in [('á', 'a'), ('é', 'e'), ('í', 'i'), ('ó', 'o'), ('ú', 'u')]:
        s = s.replace(a, b)
    return re.sub(r'[^a-z0-9\s]', '', s).strip()

rows_out = []
for t in tramites:
    tid = t['ID_Tramite']
    nombre = t['Nombre'].strip()
    costo = t['Costo'].strip()
    plazo = t['Plazo'].strip()
    reqs = [r.strip() for r in t['Requisitos'].split('|') if r.strip()]
    num_reqs = len(reqs)

    # Buscar referencia en índice
    ref = ''
    nom_norm = normalizar(nombre)
    palabras = [w for w in nom_norm.split() if len(w) > 3]

    for num, txt in indice_entries:
        txt_norm = normalizar(txt)
        if nom_norm in txt_norm or txt_norm in nom_norm:
            p_num = num.replace('N°', '').replace('Nº', '').strip()
            ref = f"Índice TUPA pág. {p_num} ('{txt[:45]}...')"
            break

    if not ref and palabras:
        for num, txt in indice_entries:
            txt_norm = normalizar(txt)
            coincidencias = sum(1 for w in palabras if w in txt_norm)
            if coincidencias >= max(2, int(len(palabras) * 0.6)):
                p_num = num.replace('N°', '').replace('Nº', '').strip()
                ref = f"Índice TUPA pág. {p_num} ('{txt[:45]}...')"
                break

    if not ref:
        ref = "No identificado en índice"

    marcado = 'sí' if tid in tramites_marcados else 'no'

    rows_out.append({
        'id_tramite': tid,
        'nombre': nombre,
        'costo_actual': costo,
        'plazo_actual': plazo,
        'numero_requisitos': num_reqs,
        'referencia_en_fuente': ref,
        'marcado': marcado,
        'req_ok': '',
        'costo_ok': '',
        'plazo_ok': ''
    })

# Ordenar primero los marcados (marcado == 'sí'), luego los no marcados
rows_out.sort(key=lambda x: (0 if x['marcado'] == 'sí' else 1, x['id_tramite']))

out_csv = 'verificacion_manual_tupa.csv'
fields = [
    'id_tramite', 'nombre', 'costo_actual', 'plazo_actual',
    'numero_requisitos', 'referencia_en_fuente', 'marcado',
    'req_ok', 'costo_ok', 'plazo_ok'
]

with open(out_csv, mode='w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows_out)

print(f"Generado exitosamente {out_csv} con {len(rows_out)} trámites.")
print(f"Marcados ('sí'): {sum(1 for r in rows_out if r['marcado'] == 'sí')}")
print(f"No marcados ('no'): {sum(1 for r in rows_out if r['marcado'] == 'no')}")
