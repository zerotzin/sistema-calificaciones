import sqlite3
import json
from datetime import datetime
from config import DB_PATH

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Tabla de alumnos por grado
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grade TEXT NOT NULL,
                name TEXT NOT NULL,
                UNIQUE(grade, name)
            )
        ''')
        
        # Tabla de entregas y calificaciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grade TEXT NOT NULL,
                student_name TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                cover_valid INTEGER NOT NULL DEFAULT 0,
                cover_details TEXT,
                quiz_score REAL DEFAULT 0.0,
                quiz_details TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Tabla de configuraciones (ej. Gemini API key)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        # Seeding inicial con algunos alumnos de prueba si la tabla está vacía
        cursor.execute('SELECT COUNT(*) as count FROM students')
        if cursor.fetchone()['count'] == 0:
            sample_students = [
                ('4', 'Alejandro Gómez Pérez'),
                ('4', 'Beatriz Hernández Ruiz'),
                ('4', 'Carlos Mendoza Soto'),
                ('5', 'Daniela Flores Castro'),
                ('5', 'Eduardo Ramírez Morales'),
                ('5', 'Fernanda Torres López'),
                ('6', 'Gabriel Navarro Silva'),
                ('6', 'Helena Vargas Ortiz'),
                ('6', 'Ignacio Delgado Cruz')
            ]
            cursor.executemany('INSERT OR IGNORE INTO students (grade, name) VALUES (?, ?)', sample_students)
            conn.commit()

def get_students_by_grade(grade: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM students WHERE grade = ? ORDER BY name ASC', (grade,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def add_student(grade: str, name: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO students (grade, name) VALUES (?, ?)', (grade, name.strip()))
        conn.commit()

def delete_student(student_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
        conn.commit()

def set_students_for_grade(grade: str, names: list):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM students WHERE grade = ?', (grade,))
        for name in names:
            if name.strip():
                cursor.execute('INSERT INTO students (grade, name) VALUES (?, ?)', (grade, name.strip()))
        conn.commit()

def create_submission(grade: str, student_name: str, filename: str, file_path: str, cover_valid: bool, cover_details: dict):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO submissions (grade, student_name, filename, file_path, cover_valid, cover_details, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (grade, student_name, filename, file_path, 1 if cover_valid else 0, json.dumps(cover_details), now))
        conn.commit()
        return cursor.lastrowid

def update_submission_quiz(submission_id: int, quiz_score: float, quiz_details: dict):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE submissions 
            SET quiz_score = ?, quiz_details = ? 
            WHERE id = ?
        ''', (quiz_score, json.dumps(quiz_details), submission_id))
        conn.commit()

def get_all_submissions():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM submissions ORDER BY id DESC')
        rows = cursor.fetchall()
        submissions = []
        for row in rows:
            sub = dict(row)
            sub['cover_details'] = json.loads(sub['cover_details']) if sub['cover_details'] else {}
            sub['quiz_details'] = json.loads(sub['quiz_details']) if sub['quiz_details'] else {}
            submissions.append(sub)
        return submissions

def delete_submission(submission_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT file_path FROM submissions WHERE id = ?', (submission_id,))
        row = cursor.fetchone()
        file_path = row['file_path'] if row else None
        
        cursor.execute('DELETE FROM submissions WHERE id = ?', (submission_id,))
        conn.commit()
        return file_path

def clear_all_submissions():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT file_path FROM submissions')
        rows = cursor.fetchall()
        file_paths = [r['file_path'] for r in rows if r['file_path']]
        
        cursor.execute('DELETE FROM submissions')
        conn.commit()
        return file_paths

def get_setting(key: str, default: str = ""):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        return row['value'] if row else default

def set_setting(key: str, value: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
        conn.commit()
