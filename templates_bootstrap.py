import os

INDEX_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Entrega de Trabajos Escolares</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen flex flex-col justify-between font-sans">
    <header class="bg-indigo-600 text-white shadow-md py-4 px-6">
        <div class="max-w-4xl mx-auto flex justify-between items-center">
            <div class="flex items-center space-x-3">
                <i class="fa-solid fa-graduation-cap text-3xl text-amber-300"></i>
                <h1 class="text-xl md:text-2xl font-bold tracking-tight">Portal de Entrega de Trabajos</h1>
            </div>
            <a href="/maestro" class="text-sm bg-indigo-700 hover:bg-indigo-800 px-3 py-1.5 rounded-lg border border-indigo-500 flex items-center gap-2 transition">
                <i class="fa-solid fa-user-tie text-amber-300"></i>
                <span>Acceso Profesor</span>
            </a>
        </div>
    </header>

    <main class="max-w-3xl mx-auto w-full px-4 py-8 flex-grow">
        <div class="bg-white rounded-2xl shadow-xl p-6 md:p-8 border border-slate-100">
            <div class="text-center mb-8">
                <span class="bg-indigo-100 text-indigo-700 text-xs font-semibold px-3 py-1 rounded-full uppercase tracking-wider">Subir Trabajo en PDF</span>
                <h2 class="text-2xl md:text-3xl font-extrabold text-slate-900 mt-2">¡Hola! Entrega tu tarea</h2>
                <p class="text-slate-500 text-sm mt-1">Selecciona tu grado, tu nombre y adjunta tu archivo en formato PDF.</p>
            </div>

            <div id="alertBox" class="hidden mb-6 p-4 rounded-xl text-sm font-medium flex items-start gap-3"></div>

            <form id="uploadForm" class="space-y-6">
                <div>
                    <label class="block text-sm font-bold text-slate-700 mb-2">
                        <i class="fa-solid fa-layer-group text-indigo-500 mr-1"></i> 1. Selecciona tu Grado Escolar:
                    </label>
                    <div class="grid grid-cols-3 gap-3">
                        <button type="button" onclick="selectGrade('4')" id="btnGrade4" class="grade-btn border-2 border-slate-200 hover:border-indigo-400 py-3 rounded-xl font-bold text-slate-700 hover:text-indigo-600 flex flex-col items-center transition">
                            <span class="text-lg">4°</span>
                            <span class="text-xs font-normal">Cuarto</span>
                        </button>
                        <button type="button" onclick="selectGrade('5')" id="btnGrade5" class="grade-btn border-2 border-slate-200 hover:border-indigo-400 py-3 rounded-xl font-bold text-slate-700 hover:text-indigo-600 flex flex-col items-center transition">
                            <span class="text-lg">5°</span>
                            <span class="text-xs font-normal">Quinto</span>
                        </button>
                        <button type="button" onclick="selectGrade('6')" id="btnGrade6" class="grade-btn border-2 border-slate-200 hover:border-indigo-400 py-3 rounded-xl font-bold text-slate-700 hover:text-indigo-600 flex flex-col items-center transition">
                            <span class="text-lg">6°</span>
                            <span class="text-xs font-normal">Sexto</span>
                        </button>
                    </div>
                    <input type="hidden" id="selectedGrade" name="grade" required>
                </div>

                <div id="studentContainer" class="opacity-50 pointer-events-none transition-all duration-300">
                    <label class="block text-sm font-bold text-slate-700 mb-2" for="studentSelect">
                        <i class="fa-solid fa-user-check text-indigo-500 mr-1"></i> 2. Selecciona tu Nombre de la lista:
                    </label>
                    <select id="studentSelect" name="student_name" class="w-full bg-slate-50 border border-slate-300 rounded-xl p-3 text-slate-800 font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                        <option value="">-- Primero selecciona tu grado --</option>
                    </select>
                </div>

                <div id="fileContainer" class="opacity-50 pointer-events-none transition-all duration-300">
                    <label class="block text-sm font-bold text-slate-700 mb-2">
                        <i class="fa-solid fa-file-pdf text-indigo-500 mr-1"></i> 3. Adjunta tu Trabajo (Solo archivo PDF):
                    </label>
                    <div class="border-2 border-dashed border-slate-300 rounded-xl p-6 text-center hover:border-indigo-400 bg-slate-50 cursor-pointer relative" onclick="document.getElementById('pdfFile').click()">
                        <i class="fa-solid fa-cloud-arrow-up text-4xl text-indigo-400 mb-2"></i>
                        <p id="fileNameDisplay" class="text-slate-600 font-medium text-sm">Haz clic aquí para seleccionar tu archivo PDF</p>
                        <p class="text-xs text-slate-400 mt-1">Asegúrate de que la primera página sea la portada con tu Nombre, Título y Trimestre.</p>
                        <input type="file" id="pdfFile" name="pdf_file" accept=".pdf" class="hidden" onchange="handleFileSelect(this)">
                    </div>
                </div>

                <div class="bg-amber-50 border border-amber-200 rounded-xl p-4 text-xs text-amber-800 flex items-start gap-2">
                    <i class="fa-solid fa-circle-info text-amber-500 text-base mt-0.5"></i>
                    <div>
                        <span class="font-bold">Recordatorio importante:</span> La primera página debe incluir tu <strong>Nombre Completo</strong>, <strong>Título de la Actividad</strong> y el <strong>Trimestre</strong>. Luego de validar tu portada, responderás un cuestionario rápido de 10 preguntas sobre tu trabajo.
                    </div>
                </div>

                <button type="submit" id="submitBtn" disabled class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3.5 px-6 rounded-xl shadow-lg hover:shadow-xl transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                    <i class="fa-solid fa-arrow-right"></i>
                    <span>Validar Portada e Iniciar Cuestionario</span>
                </button>
            </form>

            <div id="loadingOverlay" class="hidden fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex flex-col items-center justify-center text-white">
                <div class="animate-spin rounded-full h-16 w-16 border-4 border-indigo-400 border-t-transparent mb-4"></div>
                <h3 class="text-xl font-bold">Validando portada y generando examen...</h3>
                <p class="text-sm text-slate-200 mt-1">La IA está leyendo tu documento para crear tus 10 preguntas.</p>
            </div>
        </div>
    </main>

    <footer class="text-center py-4 text-xs text-slate-400 border-t border-slate-200">
        Plataforma Escolar de Entrega y Evaluación de Trabajos &copy; 2026
    </footer>

    <script>
        let selectedGradeValue = '';

        function selectGrade(grade) {
            selectedGradeValue = grade;
            document.getElementById('selectedGrade').value = grade;

            document.querySelectorAll('.grade-btn').forEach(btn => {
                btn.classList.remove('border-indigo-600', 'bg-indigo-50', 'text-indigo-700');
                btn.classList.add('border-slate-200', 'text-slate-700');
            });

            const activeBtn = document.getElementById(`btnGrade${grade}`);
            activeBtn.classList.remove('border-slate-200', 'text-slate-700');
            activeBtn.classList.add('border-indigo-600', 'bg-indigo-50', 'text-indigo-700');

            fetch(`/api/students/${grade}`)
                .then(res => res.json())
                .then(data => {
                    const select = document.getElementById('studentSelect');
                    select.innerHTML = '<option value="">-- Selecciona tu Nombre --</option>';
                    data.students.forEach(s => {
                        const opt = document.createElement('option');
                        opt.value = s.name;
                        opt.textContent = s.name;
                        select.appendChild(opt);
                    });

                    const studentContainer = document.getElementById('studentContainer');
                    studentContainer.classList.remove('opacity-50', 'pointer-events-none');
                    checkFormValid();
                })
                .catch(err => showAlert('Error al cargar la lista de alumnos.', 'error'));
        }

        document.getElementById('studentSelect').addEventListener('change', () => {
            const fileContainer = document.getElementById('fileContainer');
            if (document.getElementById('studentSelect').value) {
                fileContainer.classList.remove('opacity-50', 'pointer-events-none');
            } else {
                fileContainer.classList.add('opacity-50', 'pointer-events-none');
            }
            checkFormValid();
        });

        function handleFileSelect(input) {
            const display = document.getElementById('fileNameDisplay');
            if (input.files && input.files[0]) {
                display.innerHTML = `<i class="fa-solid fa-file-pdf text-indigo-600 mr-2"></i><strong>${input.files[0].name}</strong> (${(input.files[0].size / 1024 / 1024).toFixed(2)} MB)`;
            } else {
                display.textContent = 'Haz clic aquí para seleccionar tu archivo PDF';
            }
            checkFormValid();
        }

        function checkFormValid() {
            const grade = document.getElementById('selectedGrade').value;
            const student = document.getElementById('studentSelect').value;
            const file = document.getElementById('pdfFile').files[0];
            const btn = document.getElementById('submitBtn');

            if (grade && student && file) {
                btn.disabled = false;
            } else {
                btn.disabled = true;
            }
        }

        function showAlert(msg, type = 'info') {
            const box = document.getElementById('alertBox');
            box.classList.remove('hidden', 'bg-red-50', 'text-red-700', 'bg-green-50', 'text-green-700');
            if (type === 'error') {
                box.classList.add('bg-red-50', 'text-red-700');
                box.innerHTML = `<i class="fa-solid fa-circle-exclamation text-lg mt-0.5"></i> <div>${msg}</div>`;
            } else {
                box.classList.add('bg-green-50', 'text-green-700');
                box.innerHTML = `<i class="fa-solid fa-circle-check text-lg mt-0.5"></i> <div>${msg}</div>`;
            }
        }

        document.getElementById('uploadForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            document.getElementById('loadingOverlay').classList.remove('hidden');

            fetch('/api/upload-pdf', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                document.getElementById('loadingOverlay').classList.add('hidden');
                if (data.error) {
                    showAlert(data.error, 'error');
                } else if (!data.cover_valid) {
                    showAlert(`<strong>Revisa tu portada:</strong> ${data.cover_summary}`, 'error');
                } else {
                    sessionStorage.setItem('quiz_data', JSON.stringify(data));
                    window.location.href = '/quiz';
                }
            })
            .catch(err => {
                document.getElementById('loadingOverlay').classList.add('hidden');
                showAlert('Ocurrió un error al procesar tu archivo. Intenta de nuevo.', 'error');
            });
        });
    </script>
</body>
</html>
"""

def bootstrap_templates(target_dir: str):
    """Garantiza que la carpeta de plantillas y todos sus archivos HTML existan siempre."""
    os.makedirs(target_dir, exist_ok=True)
    
    # Leer y respaldar desde archivos locales si existen, de lo contrario usar plantilla predeterminada
    templates_files = ["index.html", "quiz.html", "result.html", "teacher.html"]
    for t_name in templates_files:
        t_path = os.path.join(target_dir, t_name)
        if not os.path.exists(t_path) or os.path.getsize(t_path) == 0:
            if t_name == "index.html":
                with open(t_path, "w", encoding="utf-8") as f:
                    f.write(INDEX_HTML)
