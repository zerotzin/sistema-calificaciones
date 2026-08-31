# Guía para Publicar el Sistema en Internet (Acceso desde Casa para Alumnos)

Esta guía explica paso a paso cómo poner la plataforma en línea para que tus alumnos de 4°, 5° y 6° grado puedan ingresar desde sus casas con un enlace URL desde su computadora, celular o tablet.

---

## Opción 1: Enlace Rápido con Localtunnel / Ngrok (Probar de inmediato sin configurar la nube)

Esta opción te permite generar un enlace público en 1 minuto desde tu propia computadora (mientras tengas prendido el programa `python main.py`).

### Pasos:
1. Asegúrate de tener corriendo la aplicación en tu computadora (`python main.py`).
2. Abre una nueva ventana de la terminal / PowerShell y ejecuta:
   ```powershell
   npx localtunnel --port 8000
   ```
3. Te generará un enlace público en pantalla, por ejemplo:
   `https://escuela-tareas-2026.localtunnel.me`
4. Copias ese enlace y se lo envías a los alumnos por WhatsApp o correo. ¡Y listo! Ellos ingresarán directamente a tu sistema.

---

## Opción 2: Publicación Gratuita 24/7 en la Nube (Render.com)

Con esta opción el sitio estará activo las 24 horas del día, los 7 días de la semana, sin necesidad de que tu computadora personal esté encendida.

### Pasos:
1. Crea una cuenta gratuita en **[Render.com](https://render.com/)**.
2. Crea un repositorio en **GitHub** con la carpeta `sistema-calificaciones`.
3. En Render, presiona **New +** -> **Web Service**.
4. Conecta tu repositorio de GitHub.
5. Configura los siguientes datos en Render:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. En la sección **Environment Variables**, agrega:
   - `TEACHER_PIN`: `1632`
   - `GEMINI_API_KEY`: *(Tu clave API de Gemini)*
7. Haz clic en **Create Web Service**. 

Render te dará un enlace público permanente con certificado SSL (ejemplo: `https://calificaciones-primaria.onrender.com`) que podrás compartir con todos tus alumnos.

---

## Opción 3: PythonAnywhere (Especializado para Profesores)

1. Crea una cuenta gratuita en **[PythonAnywhere.com](https://www.pythonanywhere.com/)**.
2. Sube la carpeta `sistema-calificaciones`.
3. En la pestaña **Web**, crea una aplicación Web usando **FastAPI / ASGI**.
4. Te otorgará un enlace personalizado como: `https://tu_usuario.pythonanywhere.com`.
