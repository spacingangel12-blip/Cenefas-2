from flask import Flask, request, jsonify, send_file, render_template
import pandas as pd
import os, io, uuid, tempfile
from parser import parse_descripcion
from generador import generar_pdf

app = Flask(__name__)

COLUMNAS_ESPERADAS = {
    'CODIGO':        ['CODIGO', 'CÓDIGO', 'COD'],
    'DESCRIPCION':   ['DESCRIPCION', 'DESCRIPCIÓN', 'DESC'],
    'PRECIO NORMAL': ['PRECIO NORMAL', 'P NORMAL', 'PRECIO REGULAR'],
    'PRECIO OFERTA': ['PRECIO OFERTA', 'P OFERTA', 'PRECIO DE OFERTA'],
    'CATEGORIA':     ['CATEGORIA', 'CATEGORÍA'],
}


def _norm(txt):
    return str(txt).strip().upper()


def leer_excel(archivo):
    """
    Lee el Excel encontrando automáticamente la fila de encabezado
    (puede variar de posición entre archivos) y mapeando las columnas
    por nombre en vez de por posición fija. Tolera columnas extra o
    faltantes (p. ej. archivos sin columna GANCHO).
    """
    crudo = pd.read_excel(archivo, header=None)

    fila_header = None
    for i in range(min(15, len(crudo))):
        valores = [_norm(v) for v in crudo.iloc[i].tolist()]
        if any(v in COLUMNAS_ESPERADAS['CODIGO'] for v in valores) and \
           any(v in COLUMNAS_ESPERADAS['DESCRIPCION'] for v in valores):
            fila_header = i
            break

    if fila_header is None:
        raise ValueError(
            'No se encontró la fila de encabezado (CODIGO / DESCRIPCION) '
            'en las primeras 15 filas del archivo.'
        )

    encabezados = [_norm(v) for v in crudo.iloc[fila_header].tolist()]
    mapeo = {}
    for canon, alias in COLUMNAS_ESPERADAS.items():
        for idx, val in enumerate(encabezados):
            if val in alias:
                mapeo[canon] = idx
                break

    faltantes = [c for c in ('CODIGO', 'DESCRIPCION', 'PRECIO OFERTA') if c not in mapeo]
    if faltantes:
        raise ValueError(f'Faltan columnas obligatorias en el Excel: {", ".join(faltantes)}')

    df_raw = crudo.iloc[fila_header + 1:].reset_index(drop=True)
    df = pd.DataFrame()
    for canon, idx in mapeo.items():
        df[canon] = df_raw[idx]

    for canon in COLUMNAS_ESPERADAS:
        if canon not in df.columns:
            df[canon] = pd.NA

    return df


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/parsear', methods=['POST'])
def parsear():
    """Recibe el Excel y devuelve las filas parseadas para mostrar en tabla."""
    if 'archivo' not in request.files:
        return jsonify({'error': 'No se recibió archivo'}), 400

    archivo = request.files['archivo']
    try:
        df_raw = leer_excel(archivo)
        df_raw = df_raw[df_raw['CODIGO'].notna() & df_raw['DESCRIPCION'].notna()]
        df_raw = df_raw[df_raw['PRECIO OFERTA'].notna()]
        df_raw = df_raw.reset_index(drop=True)
        if df_raw.empty:
            return jsonify({'error': 'No se encontraron filas válidas con código, descripción y precio de oferta.'}), 400
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
    """Recibe las filas (editadas o no) y la vigencia, devuelve el PDF."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    filas          = data.get('filas', [])
    vigencia       = data.get('vigencia', '').strip()
    mostrar_precio = data.get('mostrar_precio', True)

    if not filas:
        return jsonify({'error': 'No hay filas para generar'}), 400
    if not vigencia:
        return jsonify({'error': 'Falta la vigencia'}), 400

    tmp = os.path.join(tempfile.gettempdir(), f'cenefas_{uuid.uuid4().hex}.pdf')
    try:
        generar_pdf(filas, vigencia, tmp, mostrar_precio)
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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
