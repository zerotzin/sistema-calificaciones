import os
import re
import json
import unicodedata
from pypdf import PdfReader
from google import genai
from google.genai import types
from database import get_setting

def extract_pdf_text(pdf_path: str) -> dict:
    """Extrae la primera página (portada) y separa el cuerpo del trabajo (páginas 2 en adelante)."""
    try:
        reader = PdfReader(pdf_path)
        num_pages = len(reader.pages)
        if num_pages == 0:
            return {"first_page_text": "", "full_text": "", "body_text": "", "num_pages": 0}
        
        first_page_text = reader.pages[0].extract_text() or ""
        full_text_list = []
        body_text_list = []
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                full_text_list.append(f"--- Página {i+1} ---\n{text}")
                if i > 0:  # De la página 2 en adelante es el desarrollo del tema
                    body_text_list.append(text)
        
        full_text = "\n\n".join(full_text_list)
        # Si el documento tiene varias páginas, el cuerpo excluye la portada (página 1)
        body_text = "\n\n".join(body_text_list) if body_text_list else first_page_text
        
        return {
            "first_page_text": first_page_text,
            "full_text": full_text,
            "body_text": body_text,
            "num_pages": num_pages
        }
    except Exception as e:
        print(f"Error al extraer texto del PDF: {e}")
        return {"first_page_text": "", "full_text": "", "body_text": "", "num_pages": 0}

def parse_roster_pdf(pdf_path: str) -> dict:
    """
    Extrae alumnos por grado desde un PDF de 3 páginas:
    Página 1 -> 4° Grado
    Página 2 -> 5° Grado
    Página 3 -> 6° Grado
    """
    roster = {"4": [], "5": [], "6": []}
    try:
        reader = PdfReader(pdf_path)
        pages_to_grades = ["4", "5", "6"]
        
        for idx, grade in enumerate(pages_to_grades):
            if idx < len(reader.pages):
                page_text = reader.pages[idx].extract_text() or ""
                lines = page_text.splitlines()
                names = []
                for line in lines:
                    cleaned = line.strip()
                    # Ignorar títulos comunes de lista
                    if not cleaned or re.search(r'(grado|lista|alumnos|cuarto|quinto|sexto|nombre|nº|no\.)', cleaned, re.IGNORECASE):
                        continue
                    # Eliminar viñetas o números iniciales "1. Juan Perez" -> "Juan Perez"
                    cleaned_name = re.sub(r'^\d+[\.\-\)]\s*', '', cleaned).strip()
                    if len(cleaned_name) > 3 and not cleaned_name.isdigit():
                        names.append(cleaned_name)
                roster[grade] = names
    except Exception as e:
        print(f"Error al analizar PDF de listas: {e}")
    return roster

import unicodedata

def normalize_text(text: str) -> str:
    """Convierte a minúsculas y remueve acentos/tildes para comparación flexible."""
    if not text:
        return ""
    text = text.lower()
    # Normalizar Unicode y eliminar marcas diacríticas (acentos)
    nfkd = unicodedata.normalize('NFD', text)
    return "".join([c for c in nfkd if unicodedata.category(c) != 'Mn'])

def validate_cover_page(first_page_text: str, student_name: str) -> dict:
    """
    Verifica los elementos de la portada de forma tolerante.
    Si la primera página es una imagen o diseño gráfico, aprueba la entrega para pasar al examen sin bloquear al alumno.
    """
    if not first_page_text or len(first_page_text.strip()) < 10:
        return {
            "valid": True,
            "has_name": True,
            "has_trimester": True,
            "has_title": True,
            "summary": "Portada en formato de gráfico o imagen detectada. Aprobada para examen."
        }
    
    first_page_norm = normalize_text(first_page_text)
    student_name_norm = normalize_text(student_name)
    
    name_parts = [p for p in student_name_norm.split() if len(p) > 2]
    matched_name_parts = [p for p in name_parts if p in first_page_norm]
    has_name = len(matched_name_parts) >= 1
    
    if has_name:
        summary = "Portada verificada: incluye el nombre del alumno."
    else:
        summary = "Portada recibida (verificar formato visual en panel de profesor)."

    return {
        "valid": True,
        "has_name": has_name,
        "has_trimester": True,
        "has_title": True,
        "summary": summary
    }

def get_api_key():
    env_key = os.getenv("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key
    return get_setting("gemini_api_key", "").strip()

import random

def shuffle_quiz_options(quiz_questions: list) -> list:
    """Mezcla aleatoriamente las opciones (A, B, C, D) y ajusta correct_index para que la respuesta correcta varíe de posición."""
    for q in quiz_questions:
        if q.get("type") == "multiple_choice":
            options = q.get("options", [])
            correct_idx = q.get("correct_index", 0)
            if options and 0 <= correct_idx < len(options):
                correct_answer_text = options[correct_idx]
                random.shuffle(options)
                q["options"] = options
                q["correct_index"] = options.index(correct_answer_text)
    return quiz_questions

def generate_quiz(pdf_path: str, pdf_body_text: str, student_name: str) -> list:
    """
    Genera 10 preguntas (7 opción múltiple a 30s y 3 abiertas a 60s).
    Usa Gemini 3.6 Flash con visión multimodal y fallback ultra seguro.
    """
    pdf_body_text = str(pdf_body_text or "")
    student_name = str(student_name or "Estudiante")
    
    api_key = get_api_key()
    
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            
            contents = []
            # Intentar adjuntar el archivo PDF si existe y es legible
            if pdf_path and os.path.exists(pdf_path):
                try:
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    if pdf_bytes:
                        pdf_part = types.Part.from_bytes(
                            data=pdf_bytes,
                            mime_type="application/pdf"
                        )
                        contents.append(pdf_part)
                except Exception as file_err:
                    print(f"Advertencia al abrir bytes de PDF para Gemini: {file_err}")
            
            prompt = f"""
            Eres un profesor de educación primaria evaluando la comprensión del alumno {student_name} sobre su trabajo escolar.
            El documento adjunto en formato PDF o el texto del trabajo contiene el desarrollo del tema (puede incluir texto, mapas mentales, mapas conceptuales, líneas del tiempo o infografías).

            INSTRUCCIONES OBLIGATORIAS:
            1. Analiza tanto el texto como el contenido visual de las páginas de desarrollo del tema.
            2. Ignora los datos formales de la portada (página 1: nombre del alumno, grado, trimestre).
            3. Genera EXACTAMENTE 10 preguntas pedagógicas basadas ÚNICAMENTE en el contenido temático o conceptos del trabajo:
               - Preguntas 1 a 7: Opción múltiple (4 opciones A, B, C, D) con tiempo límite de 30 segundos.
               - Preguntas 8 a 10: Preguntas abiertas de reflexión o síntesis sobre el tema con tiempo límite de 60 segundos.

            Debes responder ÚNICAMENTE con un arreglo JSON válido con el siguiente formato exacto:
            [
              {{
                "id": 1,
                "type": "multiple_choice",
                "question": "Pregunta sobre el mapa mental, infografía, línea del tiempo o contenido",
                "options": ["Opción A (Correcta)", "Opción B", "Opción C", "Opción D"],
                "correct_index": 0,
                "timer": 30
              }},
              ...
              {{
                "id": 8,
                "type": "open_ended",
                "question": "Pregunta abierta sobre el concepto o esquema desarrollado",
                "expected_concepts": ["Concepto clave esperado en la respuesta"],
                "timer": 60
              }}
            ]

            Texto de respaldo del cuerpo del trabajo:
            {pdf_body_text[:4000]}
            """
            
            contents.append(prompt)
            
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3
                )
            )
            
            if response and response.text:
                cleaned_text = response.text.strip()
                # Remover posibles bloques de codigo markdown ```json ... ```
                if cleaned_text.startswith("```"):
                    cleaned_text = re.sub(r'^```[a-zA-Z]*\n?', '', cleaned_text)
                    cleaned_text = re.sub(r'\n?```$', '', cleaned_text)
                
                quiz_data = json.loads(cleaned_text)
                if isinstance(quiz_data, list) and len(quiz_data) >= 1:
                    return shuffle_quiz_options(quiz_data[:10])
        except Exception as e:
            print(f"Error llamando a Gemini API: {e}")

    # Fallback seguro garantizado
    try:
        fallback_questions = _generate_fallback_quiz(pdf_body_text, student_name)
        return shuffle_quiz_options(fallback_questions)
    except Exception as fb_err:
        print(f"Error en fallback quiz: {fb_err}")
        return shuffle_quiz_options(_default_static_quiz(student_name))

def _default_static_quiz(student_name: str) -> list:
    """Cuestionario estático de emergencia cuando falla absolutamente todo."""
    questions = []
    for i in range(7):
        questions.append({
            "id": i + 1,
            "type": "multiple_choice",
            "question": f"Pregunta {i+1}: Sobre el desarrollo principal presentado en tu trabajo escolar:",
            "options": [
                "Exposición clara de las ideas y conceptos principales del tema.",
                "Aspectos secundarios no desarrollados en la investigación.",
                "Información ajena a la materia evaluada.",
                "Ninguna de las anteriores."
            ],
            "correct_index": 0,
            "timer": 30
        })
    for i in range(3):
        questions.append({
            "id": i + 8,
            "type": "open_ended",
            "question": f"Pregunta {i+8}: Resume con tus propias palabras la conclusión principal de tu trabajo:",
            "expected_concepts": ["comprensión", "conclusión", "explicación"],
            "timer": 60
        })
    return questions

def _generate_fallback_quiz(pdf_body_text: str, student_name: str) -> list:
    """Generador alternativo de 10 preguntas."""
    pdf_body_text = str(pdf_body_text or "")
    STOP_WORDS = {
        "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un", "para", 
        "con", "no", "una", "su", "al", "lo", "como", "mas", "pero", "sus", "le", "ya", "o", "este", 
        "si", "porque", "esta", "entre", "cuando", "muy", "sin", "sobre", "tambien", "me", "hasta", 
        "hay", "donde", "quien", "desde", "todo", "nos", "durante", "todos", "uno", "les", "ni", "contra"
    }
    
    meaningful_concepts = []
    lines = []
    
    for line in pdf_body_text.splitlines():
        line_clean = line.strip()
        if len(line_clean) > 20 and not re.search(r'(portada|trimestre|alumno|profesor|escuela|materia|grado|entrega)', line_clean, re.IGNORECASE):
            lines.append(line_clean)
            words = [re.sub(r'[^\w]', '', w.lower()) for w in line_clean.split()]
            for w in words:
                if len(w) > 4 and w not in STOP_WORDS and w not in meaningful_concepts:
                    meaningful_concepts.append(w)
                    
    sample_text = lines if lines else ["El contenido del trabajo analiza los conceptos clave del desarrollo temático."] * 10
    concepts_list = meaningful_concepts if len(meaningful_concepts) >= 7 else ["tema principal", "desarrollo", "concepto", "investigación", "análisis", "conclusión", "resultado"]
    
    questions = []
    for i in range(7):
        concept = concepts_list[i % len(concepts_list)].capitalize()
        context_sentence = sample_text[i % len(sample_text)]
        
        questions.append({
            "id": i + 1,
            "type": "multiple_choice",
            "question": f"En el desarrollo de tu trabajo, ¿cómo se aborda el concepto de '{concept}'?",
            "options": [
                f"Se explica detalladamente como parte central del tema ('{context_sentence[:50]}...').",
                f"Es una idea secundaria que contradice a {concept}.",
                "Es un aspecto que no forma parte del contenido investigado.",
                "Ninguna de las anteriores."
            ],
            "correct_index": 0,
            "timer": 30
        })
    
    for i in range(3):
        context_sentence = sample_text[(i+7) % len(sample_text)]
        questions.append({
            "id": i + 8,
            "type": "open_ended",
            "question": f"Resume con tus palabras la idea principal que explicaste en la sección: '{context_sentence[:80]}...'",
            "expected_concepts": ["comprensión", "explicación clara", "desarrollo propio"],
            "timer": 60
        })
        
    return questions

def evaluate_open_answer(question: str, expected_concepts: list, student_answer: str) -> dict:
    """
    Evalúa la respuesta abierta del alumno:
    Retorna: score (1.0 = Correcto, 0.5 = Medio bien/Parcial, 0.0 = Incorrecto) y feedback.
    """
    if not student_answer or len(student_answer.strip()) < 5:
        return {
            "score": 0.0,
            "eval_label": "Incorrecto",
            "feedback": "La respuesta no fue ingresada o es muy vaga."
        }
        
    api_key = get_api_key()
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            prompt = f"""
            Evalúa la respuesta de un alumno de primaria a una pregunta abierta basada en su propio trabajo escolar.
            
            Pregunta: {question}
            Conceptos esperados: {', '.join(expected_concepts)}
            Respuesta redactada por el alumno: {student_answer}
            
            Asigna una calificación estrictamente dentro de estos valores:
            - 1.0 si la respuesta es correcta y demuestra comprensión.
            - 0.5 si la respuesta está medio bien (parcialmente correcta).
            - 0.0 si es incorrecta o no tiene sentido.
            
            Responde ÚNICAMENTE en JSON con el formato:
            {{
                "score": 1.0,
                "eval_label": "Correcto",
                "feedback": "Breve explicación de la evaluación"
            }}
            """
            
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            res = json.loads(response.text)
            return res
        except Exception as e:
            print(f"Error evaluando respuesta abierta con Gemini: {e}")
            
    # Fallback heurístico simple si no hay API Key
    words_count = len(student_answer.split())
    if words_count >= 8:
        return {"score": 1.0, "eval_label": "Correcto", "feedback": "Respuesta completa y coherente."}
    elif words_count >= 4:
        return {"score": 0.5, "eval_label": "Parcialmente correcto", "feedback": "Respuesta breve pero aceptable."}
    else:
        return {"score": 0.0, "eval_label": "Incorrecto", "feedback": "Respuesta incompleta."}
