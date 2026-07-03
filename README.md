# Cenefas Publicitarias

App web para generar cenefas publicitarias desde un Excel **o** escaneando códigos de barras.

## Estructura
```
cenefas_app/
├── app.py              ← servidor Flask (Excel + Escáner + API base de datos)
├── parser.py           ← parseo TIPO/MARCA/DETALLE
├── generador.py        ← generación del PDF (con y sin precio)
├── productos.db        ← base de datos SQLite (se crea automáticamente)
├── requirements.txt
├── Procfile
├── templates/
│   └── index.html      ← interfaz web (3 pestañas)
└── static/
    └── fonts/          ← tipografías PassionOne, Archivo, Montserrat
```

---

## Modos de uso

### 📊 Pestaña Excel (flujo original)
1. Sube el archivo Excel de ofertas
2. Escribe la vigencia
3. Toca **Cargar y revisar ofertas**
4. Edita TIPO/MARCA/DETALLE si hace falta
5. **Generar y descargar PDF** — cenefas **con precio**

### 📷 Pestaña Escáner
1. Escribe la vigencia
2. Activa la cámara y apunta al código de barras, o escríbelo manualmente
3. Si el código está en la base de datos → se agrega automáticamente
4. Si **no** está → aparece un formulario para añadirlo y se guarda para la próxima vez
5. **Generar y descargar PDF** — cenefas **sin precio** (zona en blanco)

### 🗄️ Pestaña Base de datos
- **Importar** un CSV o Excel con columnas `CODIGO, TIPO, MARCA, DETALLE`
- **Buscar**, **editar** y **eliminar** productos individualmente
- **Añadir** nuevos productos con el botón `+ Nuevo`

---

## Formato del archivo de importación

| CODIGO        | TIPO    | MARCA   | DETALLE          |
|---------------|---------|---------|------------------|
| 7501055300057 | SHAMPOO | PANTENE | 2EN1 400ML       |
| 7501035900035 | CREMA   | DOVE    | HUMECTANTE 200ML |

---

## Despliegue en Render

### 1. Subir a GitHub
Crea un repositorio y sube todos los archivos.

### 2. Crear servicio en Render
1. [render.com](https://render.com) → **New → Web Service**
2. Conecta el repositorio
3. Configura:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Instance Type:** Free
4. **Create Web Service**

> **Nota sobre la base de datos:** En el tier gratuito de Render, el
> disco es efímero — los datos de `productos.db` se pierden al
> reiniciar el servicio. Para persistencia real, agrega un **Render Disk**
> (plan pagado) o migra a PostgreSQL con SQLAlchemy.
> Para uso personal con reinicios ocasionales, basta con volver a
> importar el CSV tras cada reinicio.

---

## Uso de la cámara

La app usa **QuaggaJS** (incluido desde CDN), que funciona en el
navegador sin instalar nada. Requiere que el sitio esté en **HTTPS**
(Render lo provee automáticamente). En `localhost` también funciona.

Formatos de código soportados: EAN-13, EAN-8, Code 128, UPC-A, UPC-E, Code 39.
