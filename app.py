from flask import Flask, request, jsonify, send_file, render_template
import pandas as pd
import os, io, uuid, tempfile
from parser import parse_descripcion
from generador import generar_pdf

app = Flask(__name__)

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
    """Recibe las filas (editadas o no) y la vigencia, devuelve el PDF."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400

    filas    = data.get('filas', [])
    vigencia = data.get('vigencia', '').strip()

    if not filas:
        return jsonify({'error': 'No hay filas para generar'}), 400
    if not vigencia:
        return jsonify({'error': 'Falta la vigencia'}), 400

    tmp = os.path.join(tempfile.gettempdir(), f'cenefas_{uuid.uuid4().hex}.pdf')
    try:
        generar_pdf(filas, vigencia, tmp)
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
