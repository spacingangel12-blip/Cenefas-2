# Cenefas Publicitarias

App web para generar cenefas publicitarias desde un archivo Excel.

## Estructura
```
cenefas_app/
├── app.py              ← servidor Flask
├── parser.py           ← parseo TIPO/MARCA/DETALLE
├── generador.py        ← generación del PDF
├── requirements.txt
├── Procfile
├── templates/
│   └── index.html      ← interfaz web
└── static/
    └── fonts/          ← tipografías PassionOne, Archivo, Montserrat
```

---

## Despliegue en Render (paso a paso)

### 1. Subir a GitHub
1. En GitHub, crea un repositorio nuevo llamado `cenefas-app` (privado o público)
2. Sube todos estos archivos al repositorio

### 2. Crear servicio en Render
1. Entra a [render.com](https://render.com) y crea una cuenta gratuita
2. Haz clic en **New → Web Service**
3. Conecta tu cuenta de GitHub y selecciona el repositorio `cenefas-app`
4. Configura el servicio:
   - **Name:** cenefas-app
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Instance Type:** Free
5. Haz clic en **Create Web Service**

### 3. Listo
Render te dará una URL tipo `https://cenefas-app.onrender.com`.
Ábrela desde tu Android y úsala normalmente.

> **Nota:** En el tier gratuito de Render, el servicio se "duerme"
> tras 15 minutos sin uso. La primera carga después tarda ~30 segundos.
> Las siguientes son inmediatas.

---

## Uso
1. Sube el archivo Excel de ofertas
2. Escribe la vigencia (ej: `Vigencia: Fin de Semana  26 - 28  Jun 2026`)
3. Toca **Cargar y revisar ofertas**
4. Revisa la tabla — puedes editar TIPO, MARCA o DETALLE tocando la celda
5. Toca **Generar y descargar PDF**
