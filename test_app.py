import os
import unittest
from fastapi.testclient import TestClient
from main import app
from database import init_db, get_students_by_grade, create_submission, get_all_submissions
from ai_service import validate_cover_page, _generate_fallback_quiz, evaluate_open_answer

class TestSistemaCalificaciones(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def test_database_students(self):
        students_4 = get_students_by_grade('4')
        self.assertGreater(len(students_4), 0)
        self.assertTrue(any("Alejandro" in s["name"] for s in students_4))

    def test_cover_page_validation(self):
        text = "Escuela Primaria\nAlumno: Alejandro Gómez Pérez\nTema: Las Culturas Mesoamericanas\nPrimer Trimestre"
        res = validate_cover_page(text, "Alejandro Gómez Pérez")
        self.assertTrue(res["valid"])
        self.assertTrue(res["has_name"])
        self.assertTrue(res["has_trimester"])
        self.assertTrue(res["has_title"])

    def test_cover_page_validation_missing(self):
        text = "Solo un texto de tarea sin datos"
        res = validate_cover_page(text, "Beatriz Hernández")
        self.assertTrue(res["valid"])

    def test_fallback_quiz_generation(self):
        sample_text = "En el primer trimestre estudiamos las culturas mesoamericanas como los mayas y olmecas." * 5
        quiz = _generate_fallback_quiz(sample_text, "Carlos Mendoza")
        self.assertEqual(len(quiz), 10)
        self.assertEqual(quiz[0]["type"], "multiple_choice")
        self.assertEqual(quiz[0]["timer"], 30)
        self.assertEqual(quiz[7]["type"], "open_ended")
        self.assertEqual(quiz[7]["timer"], 60)

    def test_open_answer_evaluation(self):
        res = evaluate_open_answer("Explica el tema", ["tema"], "El tema principal trata de la historia mesoamericana y sus legados.")
        self.assertGreater(res["score"], 0.0)

    def test_fastapi_endpoints(self):
        client = TestClient(app)
        
        # Test index page
        res = client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Portal de Entrega", res.text)
        
        # Test student API
        res_students = client.get("/api/students/4")
        self.assertEqual(res_students.status_code, 200)
        self.assertIn("students", res_students.json())

        # Test teacher login
        res_login = client.post("/maestro/login", json={"pin": "1632"})
        self.assertEqual(res_login.status_code, 200)
        self.assertTrue(res_login.json()["success"])

if __name__ == '__main__':
    unittest.main()
