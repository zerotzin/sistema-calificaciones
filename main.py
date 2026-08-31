import os
import uuid
import shutil
from fastapi import FastAPI, Request, File, UploadFile, Form, HTTPException, Body
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import UPLOAD_DIR, TEACHER_PIN, BASE_DIR
from database import (
    init_db, get_students_by_grade, add_student, delete_student, 
    set_students_for_grade, create_submission, update_submission_quiz, 
    get_all_submissions, delete_submission, clear_all_submissions,
    get_setting, set_setting, get_db
)
from ai_service import (
    extract_pdf_text, parse_roster_pdf, validate_cover_page, 
    generate_quiz, evaluate_open_answer
)

app = FastAPI(title="Sistema de Entregas y Calificaciones")

from templates_bootstrap import bootstrap_templates

# Inicializar base de datos
init_db()

template_dir = os.path.join(BASE_DIR, "templates")
bootstrap_templates(template_dir)

templates = Jinja2Templates(directory=template_dir)

# --- RUTAS DE VISTA HTML ---

@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/quiz", response_class=HTMLResponse)
async def quiz_page(request: Request):
    return templates.TemplateResponse(request=request, name="quiz.html")

@app.get("/result", response_class=HTMLResponse)
async def result_page(request: Request):
    return templates.TemplateResponse(request=request, name="result.html")

@app.get("/maestro", response_class=HTMLResponse)
async def teacher_page(request: Request):
    return templates.TemplateResponse(request=request, name="teacher.html")

# --- APIs PARA ESTUDIANTES ---

@app.get("/api/students/{grade}")
async def get_students(grade: str):
    students = get_students_by_grade(grade)
    return {"students": students}

@app.post("/api/upload-pdf")
async def upload_pdf(
    grade: str = Form(...),
    student_name: str = Form(...),
    pdf_file: UploadFile = File(...)
):
    try:
        if not pdf_file.filename.lower().endswith(".pdf"):
            return JSONResponse({"error": "El archivo debe estar en formato PDF."}, status_code=400)
        
        grade_dir = os.path.join(UPLOAD_DIR, grade)
        os.makedirs(grade_dir, exist_ok=True)
        
        # Nombre de archivo seguro con UUID para evitar problemas de codificación en Linux
        file_ext = os.path.splitext(pdf_file.filename)[1] or ".pdf"
        safe_filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(grade_dir, safe_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(pdf_file.file, buffer)
            
        extracted = extract_pdf_text(file_path)
        first_text = extracted.get("first_page_text", "")
        full_text = extracted.get("full_text", "")
        
        if not full_text and not first_text:
            return JSONResponse({"error": "No se pudo leer el archivo PDF. Verifica que no esté dañado."}, status_code=400)
            
        cover_eval = validate_cover_page(first_text, student_name)
        
        submission_id = create_submission(
            grade=grade,
            student_name=student_name,
            filename=pdf_file.filename,
            file_path=file_path,
            cover_valid=cover_eval["valid"],
            cover_details=cover_eval
        )
        
        # Respuesta instantánea (0.2s) para evitar timeouts en la nube
        return {
            "submission_id": submission_id,
            "cover_valid": cover_eval["valid"],
            "cover_summary": cover_eval["summary"],
            "student_name": student_name,
            "grade": grade,
            "filename": pdf_file.filename
        }
    except Exception as e:
        print(f"Error en upload_pdf: {e}")
        return JSONResponse({"error": f"Ocurrió un detalle al recibir tu PDF: {str(e)}"}, status_code=500)

@app.post("/api/generate-quiz")
async def generate_quiz_api(payload: dict = Body(...)):
    submission_id = payload.get("submission_id")
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Entrega no encontrada")
            sub = dict(row)
            
        file_path = sub["file_path"]
        student_name = sub["student_name"]
        
        extracted = extract_pdf_text(file_path)
        body_text = extracted.get("body_text", "")
        
        try:
            questions = generate_quiz(file_path, body_text, student_name)
        except Exception as q_err:
            print(f"Advertencia en generate_quiz: {q_err}")
            from ai_service import _generate_fallback_quiz, shuffle_quiz_options
            questions = shuffle_quiz_options(_generate_fallback_quiz(body_text, student_name))
            
        return {"questions": questions}
    except Exception as e:
        print(f"Error generando preguntas: {e}")
        from ai_service import _default_static_quiz, shuffle_quiz_options
        return {"questions": shuffle_quiz_options(_default_static_quiz("Estudiante"))}

@app.post("/api/submit-quiz")
async def submit_quiz(payload: dict = Body(...)):
    submission_id = payload.get("submission_id")
    student_name = payload.get("student_name")
    grade = payload.get("grade")
    answers = payload.get("answers", [])
    questions = payload.get("questions", [])

    total_score = 0.0
    details = []

    # Map questions by ID
    q_map = {q["id"]: q for q in questions}

    for ans in answers:
        q_id = ans.get("question_id")
        user_val = ans.get("user_answer")
        q_obj = q_map.get(q_id, {})
        
        q_type = q_obj.get("type", "multiple_choice")
        q_text = q_obj.get("question", "")

        if q_type == "multiple_choice":
            correct_idx = q_obj.get("correct_index", 0)
            options = q_obj.get("options", [])
            
            if user_val == correct_idx:
                score = 1.0
                feedback = "Respuesta correcta."
            else:
                score = 0.0
                correct_str = options[correct_idx] if 0 <= correct_idx < len(options) else ""
                feedback = f"Incorrecto. La respuesta correcta era: '{correct_str}'."
                
            user_ans_str = options[user_val] if user_val is not None and 0 <= user_val < len(options) else "Sin respuesta"
        else:
            # Pregunta abierta
            expected = q_obj.get("expected_concepts", [])
            eval_res = evaluate_open_answer(q_text, expected, str(user_val or ""))
            score = float(eval_res.get("score", 0.0))
            feedback = eval_res.get("feedback", "")
            user_ans_str = str(user_val or "Sin respuesta")

        total_score += score
        details.append({
            "question_id": q_id,
            "question_text": q_text,
            "user_answer": user_ans_str,
            "score": score,
            "feedback": feedback
        })

    # Escala final sobre 10
    final_score = round(total_score, 1)

    # Actualizar base de datos
    update_submission_quiz(submission_id, final_score, {"score": final_score, "details": details})

    return {
        "submission_id": submission_id,
        "student_name": student_name,
        "grade": grade,
        "final_score": final_score,
        "details": details
    }

# --- APIs PARA EL PANEL DEL PROFESOR ---

@app.post("/maestro/login")
async def teacher_login(payload: dict = Body(...)):
    pin = payload.get("pin", "")
    if pin == TEACHER_PIN:
        return {"success": True}
    return {"success": False}

@app.get("/maestro/api/submissions")
async def get_submissions():
    return {"submissions": get_all_submissions()}

@app.delete("/maestro/api/submissions/{submission_id}")
async def delete_submission_api(submission_id: int):
    file_path = delete_submission(submission_id)
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error borrando archivo PDF: {e}")
    return {"success": True}

@app.delete("/maestro/api/submissions/all/purge")
async def purge_submissions_api():
    file_paths = clear_all_submissions()
    for fp in file_paths:
        if fp and os.path.exists(fp):
            try:
                os.remove(fp)
            except Exception as e:
                print(f"Error borrando PDF: {e}")
    return {"success": True}

@app.get("/maestro/download/{submission_id}")
async def download_submission(submission_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT file_path, filename FROM submissions WHERE id = ?", (submission_id,))
        row = cursor.fetchone()
        if not row or not os.path.exists(row["file_path"]):
            raise HTTPException(status_code=404, detail="Archivo no encontrado.")
        return FileResponse(path=row["file_path"], filename=row["filename"], media_type="application/pdf")

@app.post("/maestro/api/students/add")
async def add_student_api(payload: dict = Body(...)):
    add_student(payload.get("grade"), payload.get("name"))
    return {"success": True}

@app.delete("/maestro/api/students/delete/{student_id}")
async def delete_student_api(student_id: int):
    delete_student(student_id)
    return {"success": True}

@app.post("/maestro/api/students/upload-pdf")
async def upload_roster_pdf(pdf_file: UploadFile = File(...)):
    temp_path = os.path.join(UPLOAD_DIR, "temp_roster.pdf")
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(pdf_file.file, buffer)
        
    parsed_roster = parse_roster_pdf(temp_path)
    for grade, names in parsed_roster.items():
        if names:
            set_students_for_grade(grade, names)
            
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    return {"success": True, "roster": parsed_roster}

@app.get("/maestro/api/key")
async def get_key_api():
    return {"key": get_setting("gemini_api_key", "")}

@app.post("/maestro/api/key")
async def save_key_api(payload: dict = Body(...)):
    key = payload.get("key", "").strip()
    set_setting("gemini_api_key", key)
    return {"success": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
