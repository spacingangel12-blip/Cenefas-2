from flask import Flask, request, jsonify, send_file, render_template
import pandas as pd
import os, io, uuid, tempfile, sqlite3
from parser import parse_descripcion
from generador import generar_pdf

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'productos.db')

# ─────────────────────────────────────────────
#  Helpers de normalización
# ─────────────────────────────────────────────

def normalize_codigo(val):
    """Convierte notación científica/float a string de código entero.
    Ej: '2.0803636E7' → '20803636', '7.501E12' → '7501000000000'
    """
    s = str(val).strip()
    if s.lower() in ('nan', '', 'none', 'na', '#n/a'):
        return ''
    try:
        return str(int(float(s)))
    except (ValueError, OverflowError):
        return s

def normalize_col(col):
    """Quita acentos, trim y mayúsculas en nombre de columna."""
    col = col.strip().upper()
    for src, dst in [('Á','A'),('É','E'),('Í','I'),('Ó','O'),('Ú','U'),
                     ('Ñ','N'),('Ü','U')]:
        col = col.replace(src, dst)
    return col

# ─────────────────────────────────────────────
#  Base de datos SQLite
# ─────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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

def _leer_archivo(archivo, nombre):
    """Lee un archivo como DataFrame. Detecta TSV especial, CSV y Excel."""
    # Intenta como Excel real primero
    try:
        df = pd.read_excel(archivo, dtype=str, engine='openpyxl')
        return df.fillna('')
    except Exception:
        pass
    # Fallback: texto tabulado (formato exportado con encabezado '## Sheet:')
    try:
        archivo.seek(0)
        primera = archivo.readline()
        if isinstance(primera, bytes):
            primera = primera.decode('utf-8', errors='replace')
        skiprows = 2 if primera.strip().startswith('##') else 0
        archivo.seek(0)
        df = pd.read_csv(archivo, sep='\t', skiprows=skiprows, dtype=str)
        return df.fillna('')
    except Exception:
        pass
    # Último recurso: CSV estándar
    archivo.seek(0)
    df = pd.read_csv(archivo, dtype=str)
    return df.fillna('')

def _importar_df(df):
    """
    Importa un DataFrame a la BD.
    - Formato catálogo (columna DESCRIPCION presente, sin TIPO/DETALLE):
        CODIGO, DESCRIPCION → parse_descripcion → tipo/marca/detalle
        CATEGORIA/SUBCATEGORIA y MARCA se usan como respaldo.
    - Formato estándar (columnas TIPO, MARCA, DETALLE).
    Retorna (insertados, actualizados).
    """
    df.columns = [normalize_col(c) for c in df.columns]
    cols = list(df.columns)

    if 'CODIGO' not in cols:
        raise ValueError('El archivo debe tener columna CODIGO')

    # Detectar formato catálogo vs estándar
    is_catalog = 'DESCRIPCION' in cols and 'TIPO' not in cols

    insertados = actualizados = 0
    with get_db() as conn:
        for _, row in df.iterrows():
            cod = normalize_codigo(row.get('CODIGO', ''))
            if not cod:
                continue

            if is_catalog:
                descripcion  = str(row.get('DESCRIPCION', '')).strip()
                marca_col    = str(row.get('MARCA', '')).strip().upper()
                categoria    = str(row.get('CATEGORIA', '')).strip().upper()
                subcategoria = str(row.get('SUBCATEGORIA', '')).strip().upper()

                parsed  = parse_descripcion(descripcion) if descripcion else {}
                tipo    = (parsed.get('TIPO') or
                           (subcategoria if subcategoria not in ('', 'SIN SUBCATEGORIA')
                            else categoria))
                marca   = parsed.get('MARCA') or marca_col
                detalle = parsed.get('DETALLE') or descripcion[:80]
            else:
                tipo    = str(row.get('TIPO',    '')).strip().upper() if 'TIPO'    in cols else ''
                marca   = str(row.get('MARCA',   '')).strip().upper() if 'MARCA'   in cols else ''
                detalle = str(row.get('DETALLE', '')).strip().upper() if 'DETALLE' in cols else ''

            exists = conn.execute('SELECT 1 FROM productos WHERE codigo=?', (cod,)).fetchone()
            if exists:
                conn.execute('UPDATE productos SET tipo=?, marca=?, detalle=? WHERE codigo=?',
                             (tipo, marca, detalle, cod))
                actualizados += 1
            else:
                conn.execute('INSERT INTO productos (codigo, tipo, marca, detalle) VALUES (?,?,?,?)',
                             (cod, tipo, marca, detalle))
                insertados += 1
        conn.commit()

    return insertados, actualizados

def cargar_catalogo_inicial():
    """
    Al arrancar carga el catálogo desde catalogo.csv si existe.
    Solo inserta nuevos (nunca sobreescribe ediciones manuales).
    """
    base = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base, 'catalogo.csv')
    if not os.path.exists(csv_path):
        return
    try:
        df = pd.read_csv(csv_path, dtype=str).fillna('')
        ins, _ = _importar_df(df)
        print(f'[catalogo] {ins} productos nuevos cargados desde catalogo.csv')
    except Exception as e:
        print(f'[catalogo] Error cargando catalogo.csv: {e}')

init_db()
cargar_catalogo_inicial()


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
    """
    Importa CSV o Excel a la BD.
    Acepta dos formatos:
      • Estándar:  columnas CODIGO, TIPO, MARCA, DETALLE
      • Catálogo:  columnas CODIGO, DESCRIPCIÓN/DESCRIPCION, CATEGORÍA, SUBCATEGORÍA, MARCA
                   (el formato del archivo de productos de la tienda)
    También acepta el formato exportado como texto tabulado con encabezado '## Sheet:'.
    """
    if 'archivo' not in request.files:
        return jsonify({'error': 'No se recibió archivo'}), 400

    archivo = request.files['archivo']
    try:
        df = _leer_archivo(archivo, archivo.filename.lower())
        insertados, actualizados = _importar_df(df)
        return jsonify({'ok': True, 'insertados': insertados, 'actualizados': actualizados})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
