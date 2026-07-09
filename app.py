from flask import (Flask, request, jsonify, send_file,
                   render_template, redirect, url_for, flash)
from flask_login import (LoginManager, UserMixin, login_user,
                         logout_user, login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import os, io, uuid, tempfile, sqlite3, functools
from parser import parse_descripcion
from generador import generar_pdf

app = Flask(__name__)

# ─── Clave secreta ────────────────────────────────────────────────────────────
# En Render: Settings → Environment → SECRET_KEY = (valor aleatorio largo)
app.secret_key = os.environ.get('SECRET_KEY', 'cambia-esta-clave-en-produccion-2024')

# ─── Flask-Login ──────────────────────────────────────────────────────────────
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = ''

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'productos.db')

# ─── Modelo de usuario ────────────────────────────────────────────────────────
class Usuario(UserMixin):
    def __init__(self, usuario, es_admin=False):
        self.id       = usuario
        self.usuario  = usuario
        self.es_admin = bool(es_admin)

@login_manager.user_loader
def load_user(usuario):
    with get_db() as conn:
        row = conn.execute(
            'SELECT * FROM usuarios WHERE usuario = ?', (usuario,)
        ).fetchone()
    if row:
        return Usuario(row['usuario'], row['es_admin'])
    return None

# ─── Decorador solo-admin ─────────────────────────────────────────────────────
def admin_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_admin:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

# ─────────────────────────────────────────────
#  Helpers de normalización
# ─────────────────────────────────────────────

def normalize_codigo(val):
    s = str(val).strip()
    if s.lower() in ('nan', '', 'none', 'na', '#n/a'):
        return ''
    try:
        return str(int(float(s)))
    except (ValueError, OverflowError):
        return s

def normalize_col(col):
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
        conn.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                usuario   TEXT PRIMARY KEY,
                password  TEXT NOT NULL,
                es_admin  INTEGER DEFAULT 0
            )
        ''')
        conn.commit()

def sincronizar_usuarios_env():
    """
    Lee la variable de entorno USUARIOS y sincroniza la tabla de usuarios.

    Formato de USUARIOS (en Render → Environment Variables):
        usuario1:contraseña1:admin,usuario2:contraseña2,usuario3:contraseña3:admin

    Reglas:
    - Si termina en ':admin' → es administrador.
    - Al arrancar INSERTA los que no existen y ACTUALIZA contraseña/rol
      de los que ya existen, de modo que siempre refleja lo definido en la variable.
    - Si USUARIOS no está definida, crea el usuario admin/admin123 como fallback.
    """
    raw = os.environ.get('USUARIOS', '').strip()

    if not raw:
        # Fallback: crear admin por defecto solo si la BD está vacía
        with get_db() as conn:
            count = conn.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0]
            if count == 0:
                pwd = generate_password_hash('admin123')
                conn.execute(
                    'INSERT INTO usuarios (usuario, password, es_admin) VALUES (?,?,?)',
                    ('admin', pwd, 1)
                )
                conn.commit()
                print('[auth] USUARIOS no definida — usuario admin/admin123 creado.')
        return

    entradas = [e.strip() for e in raw.split(',') if e.strip()]
    with get_db() as conn:
        for entrada in entradas:
            partes = entrada.split(':')
            if len(partes) < 2:
                print(f'[auth] Entrada inválida ignorada: {entrada}')
                continue
            usuario  = partes[0].strip().lower()
            password = partes[1].strip()
            es_admin = 1 if (len(partes) >= 3 and partes[2].strip().lower() == 'admin') else 0
            if not usuario or not password:
                continue
            pwd_hash = generate_password_hash(password)
            existe = conn.execute(
                'SELECT 1 FROM usuarios WHERE usuario=?', (usuario,)
            ).fetchone()
            if existe:
                conn.execute(
                    'UPDATE usuarios SET password=?, es_admin=? WHERE usuario=?',
                    (pwd_hash, es_admin, usuario)
                )
            else:
                conn.execute(
                    'INSERT INTO usuarios (usuario, password, es_admin) VALUES (?,?,?)',
                    (usuario, pwd_hash, es_admin)
                )
            print(f'[auth] Usuario "{usuario}" sincronizado (admin={bool(es_admin)})')
        conn.commit()

def _leer_archivo(archivo, nombre):
    try:
        df = pd.read_excel(archivo, dtype=str, engine='openpyxl')
        return df.fillna('')
    except Exception:
        pass
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
    archivo.seek(0)
    df = pd.read_csv(archivo, dtype=str)
    return df.fillna('')

def _importar_df(df):
    df.columns = [normalize_col(c) for c in df.columns]
    cols = list(df.columns)
    if 'CODIGO' not in cols:
        raise ValueError('El archivo debe tener columna CODIGO')
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
sincronizar_usuarios_env()
cargar_catalogo_inicial()


# ─────────────────────────────────────────────
#  Helper: actualizar USUARIOS en Render API
# ─────────────────────────────────────────────

import urllib.request, urllib.error, json as _json

def _actualizar_render_env(nuevos_usuarios):
    """
    Llama a la API de Render para actualizar la variable USUARIOS.
    Requiere RENDER_API_KEY y RENDER_SERVICE_ID en las variables de entorno.

    nuevos_usuarios: lista de dicts [{usuario, password_plain, es_admin}, ...]
    IMPORTANTE: las contraseñas se guardan en texto plano en la variable de entorno
    (Render las cifra en reposo). En la BD local siempre se guardan hasheadas.
    """
    api_key    = os.environ.get('RENDER_API_KEY', '')
    service_id = os.environ.get('RENDER_SERVICE_ID', '')
    if not api_key or not service_id:
        return False, 'RENDER_API_KEY o RENDER_SERVICE_ID no configurados'

    # Construir el string USUARIOS
    partes = []
    for u in nuevos_usuarios:
        entry = f"{u['usuario']}:{u['password_plain']}"
        if u.get('es_admin'):
            entry += ':admin'
        partes.append(entry)
    valor_usuarios = ','.join(partes)

    # Primero leemos todas las variables actuales para no perderlas
    url_get = f'https://api.render.com/v1/services/{service_id}/env-vars'
    req_get = urllib.request.Request(
        url_get,
        headers={'Authorization': f'Bearer {api_key}', 'Accept': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req_get, timeout=10) as r:
            env_vars_raw = _json.loads(r.read().decode())
    except Exception as e:
        return False, f'Error leyendo variables de Render: {e}'

    # env_vars_raw es una lista de {"envVar": {"key":..., "value":...}}
    env_dict = {}
    for item in env_vars_raw:
        ev = item.get('envVar', item)  # compatibilidad con distintas versiones
        env_dict[ev['key']] = ev['value']

    # Actualizar solo USUARIOS
    env_dict['USUARIOS'] = valor_usuarios

    # Preparar body para PUT (reemplaza TODAS las variables)
    body_list = [{'key': k, 'value': v} for k, v in env_dict.items()]
    body_bytes = _json.dumps(body_list).encode()

    url_put = f'https://api.render.com/v1/services/{service_id}/env-vars'
    req_put = urllib.request.Request(
        url_put,
        data=body_bytes,
        method='PUT',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
    )
    try:
        with urllib.request.urlopen(req_put, timeout=10) as r:
            r.read()
        return True, 'OK'
    except urllib.error.HTTPError as e:
        return False, f'Render API error {e.code}: {e.read().decode()}'
    except Exception as e:
        return False, str(e)


def _usuarios_db_con_passwords():
    """
    Devuelve lista de usuarios con sus contraseñas en texto plano
    leyendo la variable USUARIOS del entorno (fuente de verdad).
    Retorna dict {usuario: {password_plain, es_admin}}.
    """
    raw = os.environ.get('USUARIOS', '').strip()
    resultado = {}
    for entrada in raw.split(','):
        partes = entrada.strip().split(':')
        if len(partes) < 2:
            continue
        u = partes[0].strip().lower()
        p = partes[1].strip()
        a = len(partes) >= 3 and partes[2].strip().lower() == 'admin'
        if u and p:
            resultado[u] = {'password_plain': p, 'es_admin': a}
    return resultado


# ─────────────────────────────────────────────
#  Rutas de autenticación
# ─────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        usuario  = request.form.get('usuario', '').strip().lower()
        password = request.form.get('password', '')
        with get_db() as conn:
            row = conn.execute(
                'SELECT * FROM usuarios WHERE usuario = ?', (usuario,)
            ).fetchone()
        if row and check_password_hash(row['password'], password):
            user = Usuario(row['usuario'], row['es_admin'])
            login_user(user, remember=True)
            next_page = request.args.get('next', '/')
            return redirect(next_page)
        else:
            error = '❌ Usuario o contraseña incorrectos'
    return render_template('login.html', error=error)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ─────────────────────────────────────────────
#  Panel de administración de usuarios
# ─────────────────────────────────────────────

@app.route('/admin')
@login_required
@admin_required
def admin():
    with get_db() as conn:
        usuarios = [dict(r) for r in conn.execute(
            'SELECT usuario, es_admin FROM usuarios ORDER BY es_admin DESC, usuario'
        ).fetchall()]
    render_configurado = bool(os.environ.get('RENDER_API_KEY') and
                              os.environ.get('RENDER_SERVICE_ID'))
    return render_template('admin.html', usuarios=usuarios,
                           render_configurado=render_configurado)


@app.route('/admin/usuarios', methods=['POST'])
@login_required
@admin_required
def crear_usuario():
    usuario  = request.form.get('usuario', '').strip().lower()
    password = request.form.get('password', '').strip()
    es_admin = 1 if request.form.get('es_admin') else 0

    if not usuario or not password:
        flash('Usuario y contraseña son obligatorios', 'error')
        return redirect(url_for('admin'))
    if len(password) < 6:
        flash('La contraseña debe tener al menos 6 caracteres', 'error')
        return redirect(url_for('admin'))

    # 1. Guardar en BD local
    try:
        pwd_hash = generate_password_hash(password)
        with get_db() as conn:
            conn.execute(
                'INSERT INTO usuarios (usuario, password, es_admin) VALUES (?,?,?)',
                (usuario, pwd_hash, es_admin)
            )
            conn.commit()
    except sqlite3.IntegrityError:
        flash(f'❌ El usuario "{usuario}" ya existe', 'error')
        return redirect(url_for('admin'))

    # 2. Sincronizar con Render API (actualiza variable USUARIOS)
    env_usuarios = _usuarios_db_con_passwords()
    env_usuarios[usuario] = {'password_plain': password, 'es_admin': bool(es_admin)}
    lista = [{'usuario': u, 'password_plain': d['password_plain'], 'es_admin': d['es_admin']}
             for u, d in env_usuarios.items()]
    ok, msg = _actualizar_render_env(lista)
    if ok:
        flash(f'✅ Usuario "{usuario}" creado y guardado permanentemente', 'success')
    else:
        flash(f'✅ Usuario "{usuario}" creado en esta sesión. '
              f'⚠️ No se pudo guardar en Render: {msg}', 'error')

    return redirect(url_for('admin'))


@app.route('/admin/usuarios/<usuario>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_usuario(usuario):
    if usuario == current_user.usuario:
        flash('No puedes eliminar tu propio usuario', 'error')
        return redirect(url_for('admin'))

    # 1. Borrar de BD local
    with get_db() as conn:
        conn.execute('DELETE FROM usuarios WHERE usuario = ?', (usuario,))
        conn.commit()

    # 2. Sincronizar con Render API
    env_usuarios = _usuarios_db_con_passwords()
    env_usuarios.pop(usuario, None)
    lista = [{'usuario': u, 'password_plain': d['password_plain'], 'es_admin': d['es_admin']}
             for u, d in env_usuarios.items()]
    ok, msg = _actualizar_render_env(lista)
    if ok:
        flash(f'🗑 Usuario "{usuario}" eliminado permanentemente', 'success')
    else:
        flash(f'🗑 Usuario "{usuario}" eliminado de esta sesión. '
              f'⚠️ No se pudo actualizar Render: {msg}', 'error')

    return redirect(url_for('admin'))


# ─────────────────────────────────────────────
#  Interfaz principal (protegida)
# ─────────────────────────────────────────────

@app.route('/')
@login_required
def index():
    return render_template('index.html')


# ─────────────────────────────────────────────
#  Modo Excel
# ─────────────────────────────────────────────


# Encabezados esperados (normalizados) y a qué columna canónica corresponden.
# Se aceptan variantes de acentos/espacios/mayúsculas porque normalize_col()
# ya limpia eso antes de comparar.
_ALIAS_COLUMNAS = {
    'CODIGO':        'CODIGO',
    'CLAVE':         'CODIGO',
    'DESCRIPCION':   'DESCRIPCION',
    'PRECIO NORMAL': 'PRECIO NORMAL',
    'PRECIO REGULAR':'PRECIO NORMAL',
    'PRECIO OFERTA': 'PRECIO OFERTA',
    'PRECIO PROMOCION': 'PRECIO OFERTA',
    'CATEGORIA':     'CATEGORIA',
    'GANCHO':        'GANCHO',
    'SUBCATEGORIA':  'SUBCATEGORIA',
}

def _detectar_fila_encabezado(df_sin_header, max_filas_buscar=15):
    """
    Busca, dentro de las primeras filas del archivo (leído sin header),
    la fila que contiene los encabezados reales (CODIGO/CLAVE + DESCRIPCION).
    Devuelve el índice de esa fila o None si no se encontró.
    """
    limite = min(max_filas_buscar, len(df_sin_header))
    for i in range(limite):
        valores = [normalize_col(str(v)) for v in df_sin_header.iloc[i].tolist() if str(v).strip() and str(v).lower() != 'nan']
        tiene_codigo = any(v in ('CODIGO', 'CLAVE') for v in valores)
        tiene_desc   = any(v == 'DESCRIPCION' for v in valores)
        if tiene_codigo and tiene_desc:
            return i
    return None

def _leer_excel_flexible(archivo):
    """
    Lee un Excel de oferta/cenefas con estructura variable:
    - Puede tener filas de título/vigencia antes del encabezado real.
    - El encabezado puede estar en cualquier fila dentro de las primeras ~15.
    - Puede haber una primera columna vacía usada solo para sangría.
    - Puede haber filas de "sección" (ALIMENTOS, PERFUMERIA, HOGAR, etc.)
      que solo tienen texto en la columna DESCRIPCION y todo lo demás vacío;
      esas filas se descartan porque no son productos.
    - Nombres de columnas pueden variar en acentos/espacios/mayúsculas.

    Devuelve un DataFrame con columnas canónicas:
    CODIGO, DESCRIPCION, PRECIO NORMAL, PRECIO OFERTA, CATEGORIA, GANCHO
    (las que no existan en el archivo quedan como columna vacía).
    """
    archivo.seek(0)
    crudo = pd.read_excel(archivo, header=None, dtype=str)

    fila_header = _detectar_fila_encabezado(crudo)
    if fila_header is None:
        raise ValueError(
            'No se encontró una fila de encabezado con columnas '
            '"Codigo" y "Descripcion" en las primeras filas del archivo.'
        )

    encabezados_raw = crudo.iloc[fila_header].tolist()
    datos = crudo.iloc[fila_header + 1:].reset_index(drop=True)
    datos.columns = range(len(datos.columns))

    # Mapear cada columna del archivo a su nombre canónico (o None si no aplica)
    mapa_col = {}
    for idx, encabezado in enumerate(encabezados_raw):
        texto = str(encabezado).strip()
        if not texto or texto.lower() == 'nan':
            continue
        norm = normalize_col(texto)
        canonico = _ALIAS_COLUMNAS.get(norm)
        if canonico and canonico not in mapa_col.values():
            mapa_col[idx] = canonico

    if not any(v == 'CODIGO' for v in mapa_col.values()) or \
       not any(v == 'DESCRIPCION' for v in mapa_col.values()):
        raise ValueError(
            'El archivo debe tener columnas de Código y Descripción '
            '(se aceptan encabezados como "Codigo", "Clave", "Descripcion").'
        )

    columnas_finales = ['CODIGO', 'DESCRIPCION', 'PRECIO NORMAL', 'PRECIO OFERTA', 'CATEGORIA', 'GANCHO']
    df = pd.DataFrame({col: '' for col in columnas_finales}, index=datos.index)
    for idx, canonico in mapa_col.items():
        if idx < len(datos.columns):
            df[canonico] = datos[idx]

    df = df.fillna('')

    # Descartar filas de "sección" (sin código) y filas totalmente vacías.
    df['CODIGO'] = df['CODIGO'].apply(lambda v: str(v).strip())
    df['DESCRIPCION'] = df['DESCRIPCION'].apply(lambda v: str(v).strip())
    df = df[(df['CODIGO'] != '') & (df['CODIGO'].str.lower() != 'nan') & (df['DESCRIPCION'] != '')]
    df = df.reset_index(drop=True)
    return df


@app.route('/parsear', methods=['POST'])
@login_required
def parsear():
    if 'archivo' not in request.files:
        return jsonify({'error': 'No se recibió archivo'}), 400
    archivo = request.files['archivo']
    try:
        df_raw = _leer_excel_flexible(archivo)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Error leyendo Excel: {str(e)}'}), 400

    if df_raw.empty:
        return jsonify({'error': 'No se encontraron productos con Código y Descripción en el archivo'}), 400

    filas = []
    for _, row in df_raw.iterrows():
        precio_oferta = str(row.get('PRECIO OFERTA', '')).strip()
        if not precio_oferta or precio_oferta.lower() == 'nan':
            continue  # sin precio/promoción no se genera cenefa para esa fila
        parsed = parse_descripcion(row['DESCRIPCION'])
        filas.append({
            'CODIGO':        normalize_codigo(row['CODIGO']),
            'DESCRIPCION':   str(row['DESCRIPCION']).strip(),
            'TIPO':          parsed['TIPO'],
            'MARCA':         parsed['MARCA'],
            'DETALLE':       parsed['DETALLE'],
            'PRECIO NORMAL': '' if str(row.get('PRECIO NORMAL', '')).strip().lower() in ('', 'nan') else str(row['PRECIO NORMAL']).strip(),
            'PRECIO OFERTA': precio_oferta,
        })

    if not filas:
        return jsonify({'error': 'No se encontraron filas con precio de oferta/promoción'}), 400

    return jsonify({'filas': filas})


@app.route('/generar', methods=['POST'])
@login_required
def generar():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400
    filas        = data.get('filas', [])
    vigencia     = data.get('vigencia', '').strip()
    modo         = data.get('modo', 'excel')
    sin_precio_flag = data.get('sin_precio')
    if sin_precio_flag is None:
        sin_precio_flag = (modo == 'scanner')
    if not filas:
        return jsonify({'error': 'No hay filas para generar'}), 400
    if not vigencia:
        return jsonify({'error': 'Falta la vigencia'}), 400
    tmp = os.path.join(tempfile.gettempdir(), f'cenefas_{uuid.uuid4().hex}.pdf')
    try:
        generar_pdf(filas, vigencia, tmp, sin_precio=sin_precio_flag)
        return send_file(tmp, mimetype='application/pdf',
                         as_attachment=True, download_name='Cenefas.pdf')
    except Exception as e:
        return jsonify({'error': f'Error generando PDF: {str(e)}'}), 500
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


# ─────────────────────────────────────────────
#  Modo Escáner
# ─────────────────────────────────────────────

@app.route('/buscar_codigo', methods=['GET'])
@login_required
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
    return jsonify({'encontrado': False})


# ─────────────────────────────────────────────
#  Base de datos — CRUD
# ─────────────────────────────────────────────

@app.route('/db/productos', methods=['GET'])
@login_required
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
@login_required
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
@login_required
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
@login_required
def eliminar_producto(codigo):
    with get_db() as conn:
        conn.execute('DELETE FROM productos WHERE codigo=?', (codigo,))
        conn.commit()
    return jsonify({'ok': True})


@app.route('/db/importar', methods=['POST'])
@login_required
def importar_csv():
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
