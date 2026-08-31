import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DB_PATH = os.path.join(BASE_DIR, "sistema_calificaciones.db")

# PIN maestro para el panel del profesor
TEACHER_PIN = os.getenv("TEACHER_PIN", "1632")

# API Key de Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

os.makedirs(UPLOAD_DIR, exist_ok=True)
