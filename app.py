from flask import Flask, request, jsonify, send_file, render_template
import pandas as pd
import os, io, uuid, tempfile, sqlite3
from parser import parse_descripcion
from generador import generar_pdf

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'productos.db')

# ─────────────────────────────────────────────
#  Base de datos SQLite
# ─────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'catalogo.csv')

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                codigo  TEXT PRIMARY KEY,
                tipo    TEXT DEFAULT '',
                marca   TEXT DEFAULT '',
                detalle TEXT DEFAULT ''
            )
        ''')
        conn.commit()

def cargar_catalogo_csv():
    """
    Carga catalogo.csv a la base de datos al arrancar.
    - Inserta productos nuevos (que no existan en la BD).
    - No sobreescribe productos editados manualmente.
    Si quieres forzar una actualización completa, borra productos.db antes de arrancar.
    """
    if not os.path.exists(CSV_PATH):
        return

    try:
        df = pd.read_csv(CSV_PATH, dtype=str).fillna('')
        df.columns = [c.strip().upper() for c in df.columns]
        if 'CODIGO' not in df.columns:
            print('[catalogo] El CSV no tiene columna CODIGO, se omite.')
            return

        insertados = 0
        with get_db() as conn:
            for _, row in df.iterrows():
                cod = str(row.get('CODIGO', '')).strip()
                if not cod:
                    continue
                existe = conn.execute(
                    'SELECT 1 FROM productos WHERE codigo=?', (cod,)
                ).fetchone()
                if not existe:
                    conn.execute(
                        'INSERT INTO productos (codigo, tipo, marca, detalle) VALUES (?,?,?,?)',
                        (
                            cod,
                            str(row.get('TIPO',    '')).strip().upper(),
                            str(row.get('MARCA',   '')).strip().upper(),
                            str(row.get('DETALLE', '')).strip().upper(),
                        )
                    )
                    insertados += 1
            conn.commit()
        print(f'[catalogo] {insertados} productos nuevos cargados desde catalogo.csv')
    except Exception as e:
        print(f'[catalogo] Error cargando CSV: {e}')

init_db()
cargar_catalogo_csv()


# ─────────────────────────────────────────────
#  Interfaz principal
# ─────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


# ─────────────────────────────────────────────
#  Modo Excel (flujo original)
# ─────────────────────────────────────────────

@app.route('/parsear', methods=['POST'])
def parsear():
    if 'archivo' not in request.files:
        return jsonify({'error': 'No se recibió archivo'}), 400

    archivo = request.files['archivo']
    try:
        df_raw = pd.read_excel(archivo, header=3)
        df_raw.columns = ['DROP','CODIGO','DESCRIPCION','PRECIO NORMAL','PRECIO OFERTA','CATEGORIA','GANCHO']
        df_raw = df_raw.drop(columns=['DROP'])
        df_raw = df_raw[df_raw['CODIGO'].notna() & df_raw['DESCRIPCION'].notna()]
        df_raw = df_raw[df_raw['PRECIO OFERTA'].notna()]
        df_raw = df_raw.reset_index(drop=True)
    except Exception as e:
        return jsonify({'error': f'Error leyendo Excel: {str(e)}'}), 400

    filas = []
    for _, row in df_raw.iterrows():
        parsed = parse_descripcion(row['DESCRIPCION'])
        filas.append({
            'CODIGO':        str(int(row['CODIGO'])) if pd.notna(row['CODIGO']) else '',
            'DESCRIPCION':   str(row['DESCRIPCION']).strip(),
            'TIPO':          parsed['TIPO'],
            'MARCA':         parsed['MARCA'],
            'DETALLE':       parsed['DETALLE'],
            'PRECIO NORMAL': str(row['PRECIO NORMAL']) if pd.notna(row['PRECIO NORMAL']) else '',
            'PRECIO OFERTA': str(row['PRECIO OFERTA']).strip(),
        })

    return jsonify({'filas': filas})


@app.route('/generar', methods=['POST'])
def generar():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    filas    = data.get('filas', [])
    vigencia = data.get('vigencia', '').strip()
    modo     = data.get('modo', 'excel')   # 'excel' | 'scanner'

    if not filas:
        return jsonify({'error': 'No hay filas para generar'}), 400
    if not vigencia:
        return jsonify({'error': 'Falta la vigencia'}), 400

    tmp = os.path.join(tempfile.gettempdir(), f'cenefas_{uuid.uuid4().hex}.pdf')
    try:
        generar_pdf(filas, vigencia, tmp, sin_precio=(modo == 'scanner'))
        return send_file(
            tmp,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='Cenefas.pdf'
        )
    except Exception as e:
        return jsonify({'error': f'Error generando PDF: {str(e)}'}), 500
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


# ─────────────────────────────────────────────
#  Modo Escáner — buscar código
# ─────────────────────────────────────────────

@app.route('/buscar_codigo', methods=['GET'])
def buscar_codigo():
    codigo = request.args.get('codigo', '').strip()
    if not codigo:
        return jsonify({'error': 'Código vacío'}), 400

    with get_db() as conn:
        row = conn.execute(
            'SELECT * FROM productos WHERE codigo = ?', (codigo,)
        ).fetchone()

    if row:
        return jsonify({'encontrado': True, 'producto': dict(row)})
    else:
        return jsonify({'encontrado': False})


# ─────────────────────────────────────────────
#  Base de datos — CRUD
# ─────────────────────────────────────────────

@app.route('/db/productos', methods=['GET'])
def listar_productos():
    q = request.args.get('q', '').strip()
    with get_db() as conn:
        if q:
            rows = conn.execute(
                '''SELECT * FROM productos
                   WHERE codigo LIKE ? OR marca LIKE ? OR tipo LIKE ? OR detalle LIKE ?
                   ORDER BY marca, tipo''',
                (f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%')
            ).fetchall()
        else:
            rows = conn.execute(
                'SELECT * FROM productos ORDER BY marca, tipo'
            ).fetchall()
    return jsonify({'productos': [dict(r) for r in rows]})


@app.route('/db/productos', methods=['POST'])
def crear_producto():
    d = request.get_json()
    codigo  = str(d.get('codigo',  '')).strip()
    tipo    = str(d.get('tipo',    '')).strip().upper()
    marca   = str(d.get('marca',   '')).strip().upper()
    detalle = str(d.get('detalle', '')).strip().upper()

    if not codigo:
        return jsonify({'error': 'El código es obligatorio'}), 400

    try:
        with get_db() as conn:
            conn.execute(
                'INSERT INTO productos (codigo, tipo, marca, detalle) VALUES (?,?,?,?)',
                (codigo, tipo, marca, detalle)
            )
            conn.commit()
        return jsonify({'ok': True})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Ese código ya existe'}), 409


@app.route('/db/productos/<codigo>', methods=['PUT'])
def actualizar_producto(codigo):
    d = request.get_json()
    tipo    = str(d.get('tipo',    '')).strip().upper()
    marca   = str(d.get('marca',   '')).strip().upper()
    detalle = str(d.get('detalle', '')).strip().upper()

    with get_db() as conn:
        conn.execute(
            'UPDATE productos SET tipo=?, marca=?, detalle=? WHERE codigo=?',
            (tipo, marca, detalle, codigo)
        )
        conn.commit()
    return jsonify({'ok': True})


@app.route('/db/productos/<codigo>', methods=['DELETE'])
def eliminar_producto(codigo):
    with get_db() as conn:
        conn.execute('DELETE FROM productos WHERE codigo=?', (codigo,))
        conn.commit()
    return jsonify({'ok': True})


@app.route('/db/importar', methods=['POST'])
def importar_csv():
    """Importa un CSV/Excel con columnas: CODIGO, TIPO, MARCA, DETALLE"""
    if 'archivo' not in request.files:
        return jsonify({'error': 'No se recibió archivo'}), 400

    archivo = request.files['archivo']
    nombre  = archivo.filename.lower()

    try:
        if nombre.endswith('.csv'):
            df = pd.read_csv(archivo)
        else:
            df = pd.read_excel(archivo)

        df.columns = [c.strip().upper() for c in df.columns]
        if 'CODIGO' not in df.columns:
            return jsonify({'error': 'El archivo debe tener columna CODIGO'}), 400

        insertados = 0
        actualizados = 0
        with get_db() as conn:
            for _, row in df.iterrows():
                cod = str(row.get('CODIGO', '')).strip()
                if not cod or cod == 'nan':
                    continue
                tipo    = str(row.get('TIPO',    '')).strip().upper() if 'TIPO'    in df.columns else ''
                marca   = str(row.get('MARCA',   '')).strip().upper() if 'MARCA'   in df.columns else ''
                detalle = str(row.get('DETALLE', '')).strip().upper() if 'DETALLE' in df.columns else ''

                exists = conn.execute(
                    'SELECT 1 FROM productos WHERE codigo=?', (cod,)
                ).fetchone()

                if exists:
                    conn.execute(
                        'UPDATE productos SET tipo=?, marca=?, detalle=? WHERE codigo=?',
                        (tipo, marca, detalle, cod)
                    )
                    actualizados += 1
                else:
                    conn.execute(
                        'INSERT INTO productos (codigo, tipo, marca, detalle) VALUES (?,?,?,?)',
                        (cod, tipo, marca, detalle)
                    )
                    insertados += 1
            conn.commit()

        return jsonify({
            'ok': True,
            'insertados': insertados,
            'actualizados': actualizados
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
