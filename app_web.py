import os
import sys
import json
import io
import zipfile
import streamlit as st

# Configuración de página
st.set_page_config(
    page_title="Planeador Didáctico • Acércate",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

from generador_planeaciones import generar_pdf_planeacion
from generador_rubricas import generar_pdf_rubricas
from generador_plano_didactico import generar_pdf_plano_didactico

def cargar_config():
    cfg = {"gemini_api_key": "", "maestro": "Demart Flores Ornelas", "centro": "CENTRO COMUNITARIO ACÉRCATE"}
    
    # 1. Cargar desde st.secrets (Streamlit Community Cloud)
    try:
        if "gemini_api_key" in st.secrets:
            cfg["gemini_api_key"] = st.secrets["gemini_api_key"]
        elif "GEMINI_API_KEY" in st.secrets:
            cfg["gemini_api_key"] = st.secrets["GEMINI_API_KEY"]
        if "maestro" in st.secrets:
            cfg["maestro"] = st.secrets["maestro"]
        if "centro" in st.secrets:
            cfg["centro"] = st.secrets["centro"]
    except Exception:
        pass

    # 2. Cargar desde config.json local si existe
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                cfg.update(loaded)
        except Exception:
            pass
    return cfg

def guardar_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def obtener_materiales_default(materia):
    m = materia.lower()
    if "músic" in m:
        return "Instrumentos musicales de percusión, reproductor de audio y hojas de actividades"
    elif "computa" in m or "tecnolog" in m:
        return "Computadora, software correspondiente e internet"
    elif "robót" in m or "stem" in m:
        return "Kits de robótica/sensores, computadora y hojas de diseño"
    elif "bibliotec" in m or "lectur" in m or "cuento" in m:
        return "Libros de cuentos, hojas blancas, lápices y colores"
    elif "físic" in m or "deport" in m:
        return "Conos, aros, pelotas, cuerdas y cronómetro"
    elif "art" in m:
        return "Cartulinas, pinturas, pinceles, tijeras y pegamento"
    elif "matemát" in m:
        return "Material concreto manipulable, reglas y hojas de trabajo"
    elif "ingl" in m:
        return "Tarjetas didácticas (flashcards), reproductor de audio y hojas de trabajo"
    elif "cívic" in m or "étic" in m or "histori" in m:
        return "Hojas de trabajo, papel bond, marcadores y tarjetas de casos"
    else:
        return "Hojas blancas, lápices, colores y recursos didácticos del aula"

def llamar_gemini_especiales(api_key, datos_entrada):
    from google import genai
    client = genai.Client(api_key=api_key)

    materia = datos_entrada["materia"]
    campo_formativo = datos_entrada["campo_formativo"]
    grados = datos_entrada["grados"]
    periodo = datos_entrada["periodo"]
    num_sesiones = datos_entrada["num_sesiones"]
    duracion = datos_entrada["duracion"]
    es_diagnostico = datos_entrada["es_diagnostico"]
    materiales_docente = datos_entrada["materiales"]
    instrucciones = datos_entrada["instrucciones"]
    nombre_centro = datos_entrada["nombre_centro"]
    maestro = datos_entrada["maestro"]

    regla_diagnostico = ""
    if es_diagnostico:
        regla_diagnostico = """
IMPORTANTE - SESIÓN DE DIAGNÓSTICO:
- La actividad práctica NO DEBE SER GUIADA paso a paso por el docente.
- El docente únicamente plantea la consigna o reto inicial y se dedica a OBSERVAR Y REGISTRAR en la lista de cotejo el nivel de autonomía, destreza y conocimientos previos del estudiante.
"""

    system_prompt = f"""Eres un experto en planeación curricular de la Nueva Escuela Mexicana (NEM) y el modelo pedagógico constructivista de {nombre_centro} para la asignatura de {materia} (Campo formativo: {campo_formativo}).

Debes generar la planeación didáctica para los siguientes grados seleccionados:
{json.dumps(grados, ensure_ascii=False, indent=2)}

Cada grado debe contener exactamente {num_sesiones} sesión(es). Duración por sesión: {duracion} minutos.

REGLAS PEDAGÓGICAS ESTRICTAS:
1. PERTINENCIA DISCIPLINAR ABSOLUTA (RIGUROSO):
   - Todo el contenido (PDA, secuencia didáctica, materiales, productos y evaluación) DEBE SER 100% EXCLUSIVO Y PERTINENTE A LA MATERIA DE {materia}.
   - NUNCA inventar o mezclar tecnología/computadoras a menos que la materia sea explícitamente Computación o Tecnología.
2. PDA (Proceso de Desarrollo de Aprendizaje):
   - Redactado en INFINITIVO (ej. Explorar, Identificar, Desarrollar, Expresar, Interpretar, Entonar, Experimentar...).
   - Proceso de aprendizaje real propio de {materia} con contexto de aplicación.
3. SECUENCIA DIDÁCTICA RICA Y EXPLÍCITA (PROHIBIDO PONER TIEMPOS EN ESTE TEXTO):
   - NUNCA escribir marcas de tiempo (como '(10 min)', '(25 min)', '10 min', 'Inicio (10 min)') dentro del texto de la secuencia didáctica. El tiempo se coloca ÚNICA Y EXCLUSIVAMENTE en la columna 'tiempos'.
   - Redacción altamente explícita y completa:
     * <b>Presentación y bienvenida:</b> Saludo y encuadre temático claro.
     * <b>Activación de conocimientos previos / Preguntas detonadoras:</b> 2-3 preguntas concretas que estimulen la curiosidad y análisis sobre {materia}.
     * <b>Actividad práctica vivencial / Reto autónomo:</b> Procedimiento paso a paso de lo que hace el alumno y el docente. Nombrar herramientas, libros, instrumentos o técnicas específicas.
{regla_diagnostico}
     * <b>Reflexión grupal y cierre:</b> Diálogo guiado donde los alumnos comparten hallazgos y responden a preguntas de metacognición.
4. TIEMPOS (Columna T):
   - Desglosar los minutos para cada momento sumando EXACTAMENTE {duracion} minutos (ejemplo: '5 min<br/><br/>10 min<br/><br/>25 min<br/><br/>10 min').
5. MATERIALES:
   - Utilizar los materiales indicados: '{materiales_docente}'.
6. PRODUCTOS:
   - Exclusivamente el trabajo/evidencia realizada por el ALUMNO acorde a {materia}. NUNCA registros administrativos del docente.
7. EVALUACIÓN FORMATIVA:
   - Iniciar con 'Se evalúa mediante observación directa / lista de cotejo la capacidad del alumno para...' detallando qué y cómo se evalúa el aprendizaje propio de {materia}.

Debes responder ÚNICAMENTE con un objeto JSON válido con la siguiente estructura (sin formato markdown adicional ni texto fuera del JSON):
{{
  "nombre_centro": "{nombre_centro}",
  "maestro": "{maestro}",
  "materia": "{materia}",
  "campo_formativo": "{campo_formativo}",
  "fecha_periodo": "{periodo}",
  "duracion_sesion": "{duracion}",
  "grados": [
    {{
      "grado_label": "Nombre del grado (ej. 1º de Primaria, 2º de Preescolar, etc.)",
      "grado": 1,
      "nivel": "Primaria",
      "fase": 3,
      "semanas": [
        {{
          "pda": "...",
          "secuencia": "<b>Presentación y bienvenida:</b> ...<br/><br/><b>Activación de conocimientos previos:</b> ...<br/><br/><b>Actividad práctica vivencial:</b> ...<br/><br/><b>Reflexión grupal y cierre:</b> ...",
          "tiempos": "5 min<br/><br/>10 min<br/><br/>25 min<br/><br/>10 min",
          "materiales": "{materiales_docente}",
          "productos": "...",
          "evaluacion": "Se evalúa mediante observación directa..."
        }}
      ]
    }}
  ]
}}
"""

    prompt = f"""Genera la planeación didáctica con los siguientes temas y requerimientos del docente:

Periodo: {periodo}
Materia: {materia}
Campo Formativo: {campo_formativo}
Materiales indicados: {materiales_docente}
Grados a generar: {[g['label'] for g in grados]}
Observaciones e ideas de clase:
{instrucciones}
"""

    modelos = ['gemini-3.5-flash', 'gemini-3.6-flash', 'gemini-3.7-flash', 'gemini-flash-latest']
    last_err = None

    for mod in modelos:
        try:
            res = client.models.generate_content(
                model=mod,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json"
                )
            )
            return json.loads(res.text)
        except Exception as e:
            last_err = e
            continue

    raise last_err

def llamar_gemini_plano_didactico(api_key, datos_entrada):
    from google import genai
    client = genai.Client(api_key=api_key)

    nombre_centro = datos_entrada["nombre_centro"]
    ciclo_escolar = datos_entrada["ciclo_escolar"]
    grado_str = datos_entrada["grado_str"]
    fase_grado = datos_entrada["fase_grado"]
    grupo_str = datos_entrada["grupo"]
    fecha_entrega = datos_entrada["fecha_entrega"]
    periodo_abarca = datos_entrada["periodo_abarca"]
    problematica = datos_entrada["problematica"]
    campos_formativos = datos_entrada["campos_formativos"]
    ejes_articuladores = datos_entrada["ejes_articuladores"]
    modalidad_pref = datos_entrada["modalidad_pref"]
    num_sesiones = datos_entrada["num_sesiones"]
    instrucciones = datos_entrada["instrucciones"]
    maestro = datos_entrada["maestro"]

    system_prompt = f"""Eres un experto en planeación curricular de la Nueva Escuela Mexicana (NEM) y el Programa Sintético SEP 2022 para Primaria en {nombre_centro}.

Debes generar el documento oficial PLANO DIDÁCTICO para {grado_str} ({fase_grado}).

REGLAS PEDAGÓGICAS ESTRICTAS (PROGRAMA SEP 2022):
1. VINCULACIÓN CURRICULAR EXACTA:
   - Extraer y redactar los CONTENIDOS OFICIALES y los PROCESOS DE DESARROLLO DE APRENDIZAJE (PDA) autorizados por la SEP en el Programa Sintético 2022 para los campos formativos seleccionados: {json.dumps(campos_formativos, ensure_ascii=False)}.
2. SECUENCIA DIDÁCTICA RICA, COMPLETA Y EXPLÍCITA (PROHIBIDO REPETIR TIEMPOS AQUÍ):
   - NUNCA escribir marcas ni menciones de tiempo (como '10 min', '15 min', '(10 min)', 'Inicio (10 min)', 'Desarrollo (25 min)') dentro del texto de la columna Secuencia Didáctica. El tiempo se coloca ÚNICA Y EXCLUSIVAMENTE en la columna 'tiempo'.
   - La redacción de las actividades debe ser altamente explícita, descriptiva y formativa:
     * Si hay DIÁLOGO COLECTIVO O PLENARIA: Especificar el tema exacto a debatir y redactar las preguntas orientadoras que lanza el docente para guiar la reflexión.
     * Si hay FORMULACIÓN DE HIPÓTESIS: Describir con claridad el fenómeno o situación que analizan los estudiantes, las preguntas que responden (ej. ¿Qué cambió? ¿Puede volver a su estado original?) y el formato donde registran sus hipótesis.
     * Si hay RUTINAS DE PENSAMIENTO VISIBLE (ej. 'Veo – Pienso – Me pregunto', 'Antes pensaba, ahora pienso', 'Afirmación – Evidencia – Pregunta', 'Semáforo', 'Compara y contrasta', 'Puente'): Describir el estímulo o imágenes presentadas y el proceso de pensamiento de los alumnos.
     * Si hay EXPERIMENTO O ACTIVIDAD PRÁCTICA: Detallar los materiales que manipulan, los pasos a seguir y las variables observadas.
     * Si hay CIERRE O SÍNTESIS: Describir la conclusión colectiva o producto parcial elaborado.
3. TIEMPO Y MODALIDAD:
   - En la columna 'tiempo': poner los minutos correspondientes a cada momento separados por saltos de línea (ej. '10min\\n\\n15min\\n\\n15min').
   - En la columna 'modalidad': poner 'G' (Grupal), 'E' (Equipos) o 'I' (Individual) para cada momento (ej. 'G\\n\\nE\\n\\nI'), siguiendo la preferencia: {modalidad_pref}.
4. PRODUCTO:
   - Entregables tangibles del alumno (ej. 'Cuadro comparativo de...', 'Reporte experimental de...', 'Mapa conceptual de...', 'Borrador del proyecto...', 'Tabla de propiedades').
5. EVALUACIÓN / INDICADORES:
   - Criterios claros con viñetas '✓' (ej. '✓ Identifica...', '✓ Formula hipótesis...', '✓ Participa argumentando...').

Debes responder ÚNICAMENTE con un objeto JSON válido con la siguiente estructura (sin formato markdown adicional ni texto fuera del JSON):
{{
  "nombre_centro": "{nombre_centro}",
  "ciclo_escolar": "{ciclo_escolar}",
  "grado_str": "{grado_str}",
  "fase_grado": "{fase_grado}",
  "grupo": "{grupo_str}",
  "fecha_entrega": "{fecha_entrega}",
  "periodo_abarca": "{periodo_abarca}",
  "problematica": "{problematica}",
  "campos_formativos": {json.dumps(campos_formativos, ensure_ascii=False)},
  "contenidos": [
    "Contenido oficial SEP 2022 del campo formativo principal...",
    "Contenido oficial SEP 2022 del campo formativo secundario (si aplica)..."
  ],
  "ejes_articuladores": {json.dumps(ejes_articuladores, ensure_ascii=False)},
  "perfil_egreso": "Rasgos del perfil de egreso que se favorecen con este plano didáctico...",
  "maestro": "{maestro}",
  "reviso": "Coordinación Académica",
  "vobo": "Supervisión escolar",
  "bloques": [
    {{
      "pda": "PDA oficial SEP 2022 en infinitivo...",
      "secuencia": "Sesión 1:\\nPregunta detonadora: ...\\nRutina de pensamiento: Veo – Pienso – Me pregunto\\n...",
      "tiempo": "10min\\n\\n15min",
      "modalidad": "G\\n\\nE",
      "producto": "Cuadro comparativo...",
      "evaluacion": "✓ Identifica cambios en los materiales.\\n✓ Participa con respeto."
    }}
  ]
}}
"""

    prompt = f"""Genera el Plano Didáctico para el siguiente proyecto:

Problemática detonadora: {problematica}
Campos formativos: {campos_formativos}
Ejes articuladores: {ejes_articuladores}
Número de sesiones a generar: {num_sesiones}
Ideas y desarrollo del proyecto indicados por el docente:
{instrucciones}
"""

    modelos = ['gemini-3.5-flash', 'gemini-3.6-flash', 'gemini-3.7-flash', 'gemini-flash-latest']
    last_err = None

    for mod in modelos:
        try:
            res = client.models.generate_content(
                model=mod,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json"
                )
            )
            return json.loads(res.text)
        except Exception as e:
            last_err = e
            continue

    raise last_err


# --- INTERFAZ STREAMLIT ---
cfg = cargar_config()

# Barra lateral
with st.sidebar:
    st.image("https://raw.githubusercontent.com/google/material-design-icons/master/png/action/school/materialicons/48dp/1x/baseline_school_black_48dp.png", width=48)
    st.title("Configuración")
    
    api_key_input = st.text_input(
        "🔑 Gemini API Key:",
        value=cfg.get("gemini_api_key", ""),
        type="password",
        help="Clave gratuita de Google AI Studio (https://aistudio.google.com/app/apikey)"
    )
    
    nombre_maestro = st.text_input("👤 Maestro(a):", value=cfg.get("maestro", "Demart Flores Ornelas"))
    nombre_centro = st.text_input("🏢 Centro / Escuela:", value=cfg.get("centro", "CENTRO COMUNITARIO ACÉRCATE"))
    ciclo_escolar_cfg = st.text_input("📅 Ciclo Escolar:", value="2025-2026")

    if st.button("💾 Guardar Configuración"):
        cfg["gemini_api_key"] = api_key_input
        cfg["maestro"] = nombre_maestro
        cfg["centro"] = nombre_centro
        guardar_config(cfg)
        st.success("¡Configuración guardada!")

    st.markdown("---")
    st.caption("💡 **Centro Comunitario Acércate:**\n• Clases Especiales (horizontal con rúbricas analíticas).\n• Primaria General (Plano Didáctico SEP 2022 con problemáticas, rutinas de pensamiento y firmas).")

# Encabezado Principal
st.markdown(f"<h2 style='text-align: center; margin-bottom: 0;'>{nombre_centro}</h2>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #555; margin-top: 0;'>Generador Inteligente de Planeaciones Didácticas y Rúbricas (NEM)</h4>", unsafe_allow_html=True)
st.markdown("---")

# SELECTOR DE FORMATO
tipo_formato = st.radio(
    "📌 **Selecciona el Tipo de Formato a Generar:**",
    [
        "🎨 1. Clases Especiales y Talleres (Computación, Música, Biblioteca, Educación Física, Artes, Inglés, etc.)",
        "🏫 2. Primaria General - Plano Didáctico (Maestros de Grupo / Programa Sintético SEP 2022)"
    ],
    horizontal=True
)

st.markdown("---")

api_key_actual = api_key_input.strip() or cfg.get("gemini_api_key", "").strip()

# =========================================================================
# FORMATO 1: CLASES ESPECIALES Y TALLERES
# =========================================================================
if "Clases Especiales" in tipo_formato:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📚 1. Asignatura y Campo Formativo")
        
        opciones_materia = [
            "Computación",
            "Música / Educación Musical",
            "Biblioteca y Ludoteca",
            "Lenguajes y Lectura",
            "Saberes y Pensamiento Científico / Matemáticas",
            "Inglés",
            "Educación Artística / Artes Plásticas",
            "Educación Física y Deportes",
            "Robótica y STEM",
            "Formación Cívica y Ética",
            "Otra materia..."
        ]
        
        materia_sel = st.selectbox("Selecciona la Materia o Taller:", opciones_materia)
        if materia_sel == "Otra materia...":
            materia_final = st.text_input("Escribe el nombre de la materia:", value="Música")
        else:
            materia_final = materia_sel

        campo_sugerido = "Saberes y pensamiento científico"
        if any(k in materia_final.lower() for k in ["biblioteca", "lectura", "lenguaje", "inglés", "art", "músic"]):
            campo_sugerido = "Lenguajes"
        elif any(k in materia_final.lower() for k in ["ética", "cívica", "historia", "geografía"]):
            campo_sugerido = "Ética, naturaleza y sociedades"
        elif any(k in materia_final.lower() for k in ["educación física", "saludable", "emocional", "deport"]):
            campo_sugerido = "De lo humano y lo comunitario"

        campo_formativo_final = st.text_input("Campo Formativo:", value=campo_sugerido)

    with col2:
        st.subheader("⏱️ 2. Temporalidad y Modalidad")
        periodo_input = st.text_input("Periodo o Fechas:", value="31 de agosto al 11 de septiembre del 2026")
        
        c_ses, c_dur = st.columns(2)
        with c_ses:
            num_ses_sel = st.radio("Sesiones por grado:", [2, 1], format_func=lambda x: f"{x} sesión(es) {'(Quincenal)' if x==2 else '(Semanal)'}")
        with c_dur:
            duracion_sel = st.selectbox("Duración por sesión:", [50, 30, 20, 45, 60], index=0, format_func=lambda x: f"{x} min")

        es_diagnostico_chk = st.checkbox("🎯 Es periodo de DIAGNÓSTICO (El docente plantea reto y observa sin guiar)", value=True)

    # Sección de Materiales
    st.subheader("📦 3. Materiales y Recursos Didácticos")
    materiales_default = obtener_materiales_default(materia_final)
    materiales_input = st.text_input(
        "Especifica los materiales que se utilizarán (puedes editarlos o escribir los tuyos):",
        value=materiales_default
    )

    # Sección de Grados
    st.subheader("🎓 4. Selecciona los Grados a Planear")

    lista_grados_disponibles = [
        {"label": "1º Preescolar (Fase 2)", "grado": 1, "nivel": "Preescolar", "fase": 2},
        {"label": "2º Preescolar (Fase 2)", "grado": 2, "nivel": "Preescolar", "fase": 2},
        {"label": "3º Preescolar (Fase 2)", "grado": 3, "nivel": "Preescolar", "fase": 2},
        {"label": "1º Primaria (Fase 3)", "grado": 1, "nivel": "Primaria", "fase": 3},
        {"label": "2º Primaria (Fase 3)", "grado": 2, "nivel": "Primaria", "fase": 3},
        {"label": "3º Primaria (Fase 4)", "grado": 3, "nivel": "Primaria", "fase": 4},
        {"label": "4º Primaria (Fase 4)", "grado": 4, "nivel": "Primaria", "fase": 4},
        {"label": "5º Primaria (Fase 5)", "grado": 5, "nivel": "Primaria", "fase": 5},
        {"label": "6º Primaria (Fase 5)", "grado": 6, "nivel": "Primaria", "fase": 5},
        {"label": "1º Secundaria (Fase 6)", "grado": 1, "nivel": "Secundaria", "fase": 6},
        {"label": "2º Secundaria (Fase 6)", "grado": 2, "nivel": "Secundaria", "fase": 6},
        {"label": "3º Secundaria (Fase 6)", "grado": 3, "nivel": "Secundaria", "fase": 6},
    ]

    default_primaria = [g["label"] for g in lista_grados_disponibles if g["nivel"] == "Primaria"]

    grados_seleccionados_labels = st.multiselect(
        "Selecciona los grados que impartes (puedes agregar o quitar):",
        options=[g["label"] for g in lista_grados_disponibles],
        default=default_primaria
    )

    grados_finales = [g for g in lista_grados_disponibles if g["label"] in grados_seleccionados_labels]

    # Sección de Ideas
    st.subheader("📝 5. Ideas, Temas o Actividades del Docente")
    st.caption("Solo anota brevemente los temas o actividades clave para cada grado. Gemini redactará las secuencias completas, preguntas detonadoras y criterios propios de la materia.")

    if "músic" in materia_final.lower():
        placeholder_ejemplo = """1º: Reconocimiento del pulso corporal con palmadas y sonidos de instrumentos de percusión.
2º: Identificación de sonidos graves y agudos mediante juego de ecos rítmicos.
3º: Práctica con claves y panderos siguiendo una secuencia rítmica estructurada.
4º: Exploración de notas en flauta dulce o xilófono y lectura básica de figuras rítmicas.
5º: Ensamble instrumental en equipo combinando percusión y canto coral.
6º: Creación de un patrón rítmico propio en compás de 4 tiempos y presentación al grupo."""
    elif "bibliotec" in materia_final.lower() or "lectur" in materia_final.lower():
        placeholder_ejemplo = """1º: Presentación de la biblioteca y lectura en voz alta del cuento con títeres.
2º: Exploración guiada de libros ilustrados y formulación de predicciones del desenlace.
3º: Lectura compartida y respuesta a preguntas de comprensión literal e inferencial.
4º: Dinámica de entrevista express sobre hábitos lectores y libro favorito.
5º: Elaboración de un escudo personal con compromisos lectores del ciclo escolar.
6º: Análisis crítico de fábulas e identificación de la moraleja con lluvia de ideas."""
    else:
        placeholder_ejemplo = """1º: Familiarización con el aula y juego libre de motricidad.
2º: Actividad interactiva de resolución de retos en equipo.
3º: Elaboración de composición creativa y expresión de vivencias cotidianas.
4º: Redacción propia y aplicación de pautas estructuradas de trabajo.
5º: Reto colaborativo con acuerdos grupales y listas organizadas.
6º: Investigación y síntesis de un tema de relevancia con fuentes de consulta."""

    instrucciones_input = st.text_area(
        "Escribe tus notas aquí:",
        value=placeholder_ejemplo,
        height=140
    )

    st.markdown("---")
    btn_generar_esp = st.button("🚀 Generar Planeación y Rúbricas Oficiales (2 PDFs)", type="primary", use_container_width=True)

    if btn_generar_esp:
        if not api_key_actual:
            st.error("❌ Falta la Gemini API Key. Ingrésala en la barra lateral izquierda.")
        elif not grados_finales:
            st.error("❌ Por favor selecciona al menos un grado escolar.")
        elif not instrucciones_input.strip():
            st.error("❌ Por favor escribe las ideas o temas a desarrollar.")
        else:
            with st.spinner(f"🤖 Conectando con Gemini para redactar la planeación de {materia_final} y diseñar rúbricas..."):
                datos_entrada = {
                    "materia": materia_final,
                    "campo_formativo": campo_formativo_final,
                    "grados": grados_finales,
                    "periodo": periodo_input,
                    "num_sesiones": num_ses_sel,
                    "duracion": duracion_sel,
                    "es_diagnostico": es_diagnostico_chk,
                    "materiales": materiales_input,
                    "instrucciones": instrucciones_input,
                    "nombre_centro": nombre_centro,
                    "maestro": nombre_maestro
                }

                try:
                    resultado_json = llamar_gemini_especiales(api_key_actual, datos_entrada)

                    clean_per = periodo_input.replace(" ", "_").replace("/", "-")
                    pdf_plan_path = os.path.join(BASE_DIR, f"Planeacion_{clean_per}.pdf")
                    pdf_rub_path = os.path.join(BASE_DIR, f"Rubricas_{clean_per}.pdf")

                    generar_pdf_planeacion(resultado_json, pdf_plan_path)
                    generar_pdf_rubricas(resultado_json, pdf_rub_path)

                    with open(pdf_plan_path, "rb") as f_plan:
                        bytes_plan = f_plan.read()
                    with open(pdf_rub_path, "rb") as f_rub:
                        bytes_rub = f_rub.read()

                    # Empaquetar ambos PDFs en un archivo ZIP descargable con 1 solo clic
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        zip_file.writestr(f"Planeacion_{materia_final}_{clean_per}.pdf", bytes_plan)
                        zip_file.writestr(f"Rubricas_{materia_final}_{clean_per}.pdf", bytes_rub)
                    bytes_zip = zip_buffer.getvalue()

                    # Guardar en session_state para persistencia total contra recargas
                    st.session_state["esp_generado"] = True
                    st.session_state["esp_bytes_plan"] = bytes_plan
                    st.session_state["esp_bytes_rub"] = bytes_rub
                    st.session_state["esp_bytes_zip"] = bytes_zip
                    st.session_state["esp_nom_plan"] = f"Planeacion_{materia_final}_{clean_per}.pdf"
                    st.session_state["esp_nom_rub"] = f"Rubricas_{materia_final}_{clean_per}.pdf"
                    st.session_state["esp_nom_zip"] = f"Paquete_Planeacion_y_Rubricas_{materia_final}_{clean_per}.zip"
                    st.session_state["esp_resultado_json"] = resultado_json
                    st.rerun()

                except Exception as ex:
                    st.error(f"❌ Ocurrió un error al generar: {str(ex)}")

    # RENDERIZAR RESULTADOS Y BOTONES DE DESCARGA DESDE SESSION_STATE (PERSISTENTE)
    if st.session_state.get("esp_generado", False):
        st.markdown("---")
        st.success("🎉 ¡Documentos generados exitosamente con el formato oficial de Acércate!")

        st.markdown("#### 📥 Elige cómo deseas descargar tus documentos:")

        # Botón 1: Descargar ambos juntos en ZIP (1 solo clic)
        st.download_button(
            label="📦 Descargar AMBOS Documentos (ZIP con Planeación + Rúbricas)",
            data=st.session_state["esp_bytes_zip"],
            file_name=st.session_state["esp_nom_zip"],
            mime="application/zip",
            type="primary",
            use_container_width=True
        )

        # Botones individuales lado a lado
        c_d1, c_d2 = st.columns(2)
        with c_d1:
            st.download_button(
                label="📄 Descargar solo Planeación (PDF)",
                data=st.session_state["esp_bytes_plan"],
                file_name=st.session_state["esp_nom_plan"],
                mime="application/pdf",
                use_container_width=True
            )
        with c_d2:
            st.download_button(
                label="📋 Descargar solo Rúbricas (PDF)",
                data=st.session_state["esp_bytes_rub"],
                file_name=st.session_state["esp_nom_rub"],
                mime="application/pdf",
                use_container_width=True
            )

        if st.button("🔄 Generar Nueva Planeación (Limpiar / Reiniciar)", key="btn_reset_esp"):
            st.session_state["esp_generado"] = False
            st.rerun()

        with st.expander("👁️ Ver desglose pedagógico generado"):
            st.json(st.session_state["esp_resultado_json"])

# =========================================================================
# FORMATO 2: PRIMARIA GENERAL (PLANO DIDÁCTICO SEP 2022)
# =========================================================================
else:
    st.subheader("🏫 Configuración del Plano Didáctico (NEM SEP 2022)")
    
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        grados_plano_dict = {
            "1º de Primaria (Fase 3)": {"grado_str": "PRIMER GRADO", "fase_grado": "3 / 1°"},
            "2º de Primaria (Fase 3)": {"grado_str": "SEGUNDO GRADO", "fase_grado": "3 / 2°"},
            "3º de Primaria (Fase 4)": {"grado_str": "TERCER GRADO", "fase_grado": "4 / 3°"},
            "4º de Primaria (Fase 4)": {"grado_str": "CUARTO GRADO", "fase_grado": "4 / 4°"},
            "5º de Primaria (Fase 5)": {"grado_str": "QUINTO GRADO", "fase_grado": "5 / 5°"},
            "6º de Primaria (Fase 5)": {"grado_str": "SEXTO GRADO", "fase_grado": "5 / 6°"},
        }
        grado_plano_sel = st.selectbox("Grado y Fase de Primaria:", list(grados_plano_dict.keys()), index=5)
        grupo_plano = st.selectbox("Grupo:", ["A", "B", "C", "Único"])

    with col_p2:
        fecha_entrega_plano = st.text_input("Fecha de entrega:", value="05/junio/2026")
        periodo_abarca_plano = st.text_input("Periodo que abarca:", value="Del 08 al 19 de junio")

    with col_p3:
        num_sesiones_plano = st.number_input("Número de sesiones / momentos a desglosar:", min_value=3, max_value=20, value=8)
        modalidad_plano = st.selectbox(
            "Modalidad de Trabajo:",
            [
                "Mixta (G, E, I según cada momento - Recomendado)",
                "Grupal predominante (G)",
                "En Equipos / Parejas (E)",
                "Individual (I)"
            ]
        )

    st.markdown("---")
    st.subheader("🎯 1. Problemática / Situación Detonadora")
    problematica_input = st.text_area(
        "Describe la problemática comunitaria o pregunta detonadora del proyecto:",
        value="¿Por qué cambian los materiales y cómo podemos cuidar nuestra salud y el ambiente?",
        height=70
    )

    col_cur1, col_cur2 = st.columns(2)

    with col_cur1:
        st.subheader("🧪 2. Campos Formativos (Selecciona 1 o más)")
        opciones_campos = [
            "Saberes y Pensamiento Científico",
            "Lenguajes",
            "Ética, Naturaleza y Sociedades",
            "De lo Humano y lo Comunitario"
        ]
        campos_sel = st.multiselect(
            "Campos Formativos integrados:",
            options=opciones_campos,
            default=["Saberes y Pensamiento Científico", "De lo Humano y lo Comunitario"]
        )

    with col_cur2:
        st.subheader("🧭 3. Ejes Articuladores (Selecciona los aplicables)")
        opciones_ejes = [
            "Pensamiento crítico",
            "Vida saludable",
            "Inclusión",
            "Interculturalidad crítica",
            "Igualdad de género",
            "Apropiación de las culturas a través de la lectura y la escritura",
            "Artes y experiencias estéticas"
        ]
        ejes_sel = st.multiselect(
            "Ejes Articuladores del proyecto:",
            options=opciones_ejes,
            default=["Pensamiento crítico", "Vida saludable", "Inclusión", "Interculturalidad crítica"]
        )

    st.subheader("📝 4. Ideas, Experimentos y Actividades del Docente")
    st.caption("Anota los temas, experimentos, lecturas o productos que deseas incluir. Gemini extraerá los PDAs oficiales SEP 2022, redactará las rutinas de pensamiento (Veo-Pienso-Me pregunto, etc.), distribuirá los minutos y asignará las modalidades (G/E/I).")

    ejemplo_plano_txt = """• Observación y debate sobre combustión y oxidación de materiales (manzana, clavo, madera quemada).
• Rutinas de pensamiento visible: 'Veo - Pienso - Me pregunto' y 'Antes pensaba, ahora pienso'.
• Experimento guiado: ¿Por qué una vela se apaga al cubrirla con un vaso de vidrio? Registro científico de hipótesis y resultados.
• Análisis de etiquetas de alimentos procesados y ultraprocesados (conservadores y antioxidantes).
• Cuadro comparativo entre cambios temporales y permanentes.
• Producto final: Tríptico o infografía comunitaria sobre cuidado de la salud y prevención de contaminación."""

    instrucciones_plano_input = st.text_area("Notas del proyecto:", value=ejemplo_plano_txt, height=150)

    st.markdown("---")
    btn_generar_plano = st.button("🚀 Generar Plano Didáctico Oficial (PDF)", type="primary", use_container_width=True)

    if btn_generar_plano:
        if not api_key_actual:
            st.error("❌ Falta la Gemini API Key. Ingrésala en la barra lateral izquierda.")
        elif not campos_sel:
            st.error("❌ Selecciona al menos un Campo Formativo.")
        elif not ejes_sel:
            st.error("❌ Selecciona al menos un Eje Articulador.")
        elif not instrucciones_plano_input.strip():
            st.error("❌ Por favor escribe las notas del proyecto.")
        else:
            with st.spinner("🤖 Consultando Programa Sintético SEP 2022 y estructurando el Plano Didáctico..."):
                info_grado_plano = grados_plano_dict[grado_plano_sel]

                datos_entrada_plano = {
                    "nombre_centro": nombre_centro,
                    "ciclo_escolar": ciclo_escolar_cfg,
                    "grado_str": info_grado_plano["grado_str"],
                    "fase_grado": info_grado_plano["fase_grado"],
                    "grupo": grupo_plano,
                    "fecha_entrega": fecha_entrega_plano,
                    "periodo_abarca": periodo_abarca_plano,
                    "problematica": problematica_input,
                    "campos_formativos": campos_sel,
                    "ejes_articuladores": ejes_sel,
                    "modalidad_pref": modalidad_plano,
                    "num_sesiones": num_sesiones_plano,
                    "instrucciones": instrucciones_plano_input,
                    "maestro": nombre_maestro
                }

                try:
                    resultado_plano_json = llamar_gemini_plano_didactico(api_key_actual, datos_entrada_plano)

                    clean_nom = f"Plano_Didactico_{info_grado_plano['grado_str'].replace(' ', '_')}_{grupo_plano}"
                    pdf_plano_path = os.path.join(BASE_DIR, f"{clean_nom}.pdf")

                    generar_pdf_plano_didactico(resultado_plano_json, pdf_plano_path)

                    with open(pdf_plano_path, "rb") as f_plano:
                        bytes_plano = f_plano.read()

                    st.session_state["plano_generado"] = True
                    st.session_state["plano_bytes"] = bytes_plano
                    st.session_state["plano_nom"] = f"{clean_nom}.pdf"
                    st.session_state["plano_resultado_json"] = resultado_plano_json
                    st.rerun()

                except Exception as ex:
                    st.error(f"❌ Ocurrió un error al generar: {str(ex)}")

    # RENDERIZAR RESULTADOS Y BOTÓN DE DESCARGA DESDE SESSION_STATE (PERSISTENTE)
    if st.session_state.get("plano_generado", False):
        st.markdown("---")
        st.success("🎉 ¡Plano Didáctico oficial generado exitosamente!")
        st.download_button(
            label="📥 Descargar Plano Didáctico Oficial (PDF)",
            data=st.session_state["plano_bytes"],
            file_name=st.session_state["plano_nom"],
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

        if st.button("🔄 Generar Nuevo Plano Didáctico (Limpiar / Reiniciar)", key="btn_reset_plano"):
            st.session_state["plano_generado"] = False
            st.rerun()

        with st.expander("👁️ Ver desglose curricular oficial generado (SEP 2022)"):
            st.json(st.session_state["plano_resultado_json"])
