# lecturas_app.py - LecturApp: Modo Juego COMPLETO con búsqueda mejorada y OCR automático

import streamlit as st
import json
import os
import random
import time
import requests
import fitz  # PyMuPDF
from serpapi import GoogleSearch
from cryptography.fernet import Fernet
from openai import OpenAI
from PIL import Image
import pytesseract
from io import BytesIO

# Configuración de página
st.set_page_config(page_title="LecturApp: Modo Juego", page_icon="📚")

# Rutas y claves
QUIZ_DB = "registro_quizzes.json"
SABIAS_QUE = "sabias_que.json"
ASSETS_PATH = "assets"
PDF_FOLDER = "libros_cifrados"
os.makedirs(PDF_FOLDER, exist_ok=True)

# Claves desde secrets
FERNET_KEY = st.secrets["FERNET_KEY"]
SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
cipher = Fernet(FERNET_KEY.encode())
client = OpenAI(api_key=OPENAI_KEY)

# Crear archivos base si no existen
if not os.path.exists(QUIZ_DB):
    with open(QUIZ_DB, "w") as f:
        json.dump({}, f)
if not os.path.exists(SABIAS_QUE):
    with open(SABIAS_QUE, "w") as f:
        json.dump({}, f)

# --- Funciones auxiliares ---
def cargar_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def guardar_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def buscar_pdf_google(titulo, autor, editorial):
    queries = [
        f"{titulo} {autor} {editorial} filetype:pdf",
        f"{titulo} pdf",
        f"{titulo} libro completo filetype:pdf"
    ]
    for q in queries:
        params = {"q": q, "hl": "es", "gl": "cl", "api_key": SERPAPI_KEY}
        search = GoogleSearch(params)
        results = search.get_dict().get("organic_results", [])
        for r in results:
            link = r.get("link", "")
            if link.lower().endswith(".pdf"):
                return link
    return None

def descargar_pdf(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
    except:
        return None

def cifrar_y_guardar_pdf(titulo, pdf_bytes):
    nombre = os.path.join(PDF_FOLDER, f"{titulo.lower().replace(' ', '_')}.enc")
    if not os.path.exists(nombre):
        cifrado = cipher.encrypt(pdf_bytes)
        with open(nombre, "wb") as f:
            f.write(cifrado)
    return nombre

def cargar_pdf_cifrado(titulo):
    nombre = os.path.join(PDF_FOLDER, f"{titulo.lower().replace(' ', '_')}.enc")
    if os.path.exists(nombre):
        with open(nombre, "rb") as f:
            cifrado = f.read()
        return cipher.decrypt(cifrado)
    return None

def extraer_texto_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    texto = ""
    for page in doc:
        txt = page.get_text()
        if not txt.strip():
            pix = page.get_pixmap()
            img = Image.open(BytesIO(pix.tobytes()))
            txt = pytesseract.image_to_string(img, lang='spa')
        texto += txt + "\n"
    return texto

def generar_preguntas_ai(texto, cantidad):
    prompt = (
        f"Genera {cantidad} preguntas de opción múltiple basadas en este texto. "
        "Mitad literales y mitad interpretativas. En español latino. Formato "
        "JSON con 'pregunta', 'opciones', 'respuesta_correcta'.\nTexto:\n" + texto[:3000]
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500
        )
        contenido = response.choices[0].message.content
        preguntas = json.loads(contenido)
        return preguntas
    except Exception as e:
        print(f"[Error al generar preguntas] {e}")
        return []

def nombre_valido(nombre):
    palabras_prohibidas = ["malo", "tonto", "fuck", "shit", "puta", "mierda"]
    return not any(p in nombre.lower() for p in palabras_prohibidas)

# --- Interfaz ---
st.title("📚 LecturApp: Modo Juego")

opcion = st.radio("¿Qué quieres hacer?", ["🎮 Crear sala de juego", "👥 Unirse a una sala existente"])

if "sala_codigo" not in st.session_state:
    st.session_state.update({
        "sala_codigo": "",
        "jugador": "",
        "curso": "",
        "quiz_generado": False,
        "en_juego": False,
        "pregunta_actual": 0,
        "puntaje": 0,
        "quiz_preguntas": []
    })

if opcion == "🎮 Crear sala de juego":
    st.subheader("Crear nueva sala")
    nombre = st.text_input("Tu nombre")
    curso = st.selectbox("Curso", ["Tercero Básico", "Cuarto Básico", "Quinto Básico", "Sexto Básico"])
    if st.button("Crear sala"):
        if not nombre_valido(nombre):
            st.warning("Nombre no permitido.")
        else:
            codigo = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=5))
            st.session_state.update({
                "sala_codigo": codigo,
                "jugador": nombre,
                "curso": curso,
                "quiz_generado": False
            })

if opcion == "👥 Unirse a una sala existente":
    st.subheader("Unirse a sala")
    nombre = st.text_input("Tu nombre")
    codigo = st.text_input("Código de sala")
    if st.button("Unirme"):
        if not nombre_valido(nombre):
            st.warning("Nombre no permitido.")
        elif not codigo:
            st.warning("Debes ingresar un código válido.")
        else:
            st.session_state.update({"sala_codigo": codigo, "jugador": nombre, "quiz_generado": False})

# --- Flujo principal ---
if st.session_state.sala_codigo and st.session_state.jugador:
    st.markdown(f"### ✅ Jugador: {st.session_state.jugador}")
    st.markdown(f"### ✅ Sala: {st.session_state.sala_codigo}")
    if st.session_state.curso:
        st.markdown(f"### ✅ Curso: {st.session_state.curso}")

    quizzes = cargar_json(QUIZ_DB)
    clave_libro = None

    if opcion == "🎮 Crear sala de juego" and not st.session_state.quiz_generado:
        st.markdown("---")
        st.subheader("📚 Configura tu quiz de lectura")

        libro = st.text_input("Nombre del libro")
        autor = st.text_input("Autor")
        editorial = st.text_input("Editorial")
        cantidad = st.selectbox("¿Cuántas preguntas quieres generar?", [30, 40, 50])

        if libro:
            clave_libro = f"{st.session_state.curso} | {libro.strip().lower()}"

        if clave_libro in quizzes:
            if st.button("📂 Usar quiz existente"):
                st.session_state.quiz_generado = True
                st.session_state.quiz_preguntas = quizzes[clave_libro]["preguntas"]
                st.success("Quiz cargado desde la base de datos.")
        elif libro and autor and editorial:
            # Intentar cargar PDF desde repositorio local cifrado
            pdf_data = cargar_pdf_cifrado(libro)
            if not pdf_data:
                with st.spinner("🔍 Buscando PDF en internet..."):
                    link = buscar_pdf_google(libro, autor, editorial)
                    pdf_data = descargar_pdf(link) if link else None

            if not pdf_data:
                st.warning("No se encontró PDF online. Puedes subir el archivo manualmente.")
                uploaded = st.file_uploader("Sube el PDF del libro", type=["pdf"])
                if uploaded is not None:
                    pdf_data = uploaded.read()

            if pdf_data:
                texto = extraer_texto_pdf(pdf_data)
                preguntas = generar_preguntas_ai(texto, cantidad)
                if preguntas:
                    cifrar_y_guardar_pdf(libro, pdf_data)
                    quizzes[clave_libro] = {
                        "libro": libro,
                        "autor": autor,
                        "editorial": editorial,
                        "curso": st.session_state.curso,
                        "cantidad": cantidad,
                        "preguntas": preguntas
                    }
                    guardar_json(QUIZ_DB, quizzes)
                    st.session_state.quiz_generado = True
                    st.session_state.quiz_preguntas = preguntas
                    st.success("✅ Quiz creado exitosamente.")
                else:
                    st.error("No se pudieron generar preguntas del texto.")
            else:
                st.error("No hay PDF disponible para generar preguntas.")

    if st.session_state.quiz_generado and not st.session_state.en_juego:
        st.markdown("## 🎮 ¡Listo para jugar!")
        if st.button("Iniciar juego"):
            st.session_state.en_juego = True
            st.session_state.pregunta_actual = 0
            st.session_state.puntaje = 0
            st.rerun()

    if st.session_state.en_juego:
        st.markdown("---")
        st.header("🧠 Pregunta en juego")
        preguntas = st.session_state.quiz_preguntas
        idx = st.session_state.pregunta_actual
        if idx < len(preguntas):
            p = preguntas[idx]
            st.write(f"**{p['pregunta']}**")
            opciones = p["opciones"]
            seleccion = st.radio("Selecciona una opción:", opciones, key=f"q{idx}")
            if st.button("Responder", key=f"resp{idx}"):
                correcta = opciones[p["respuesta_correcta"]]
                if seleccion == correcta:
                    st.success("✅ ¡Correcto!")
                    st.session_state.puntaje += 1
                else:
                    st.error(f"❌ Incorrecto. La respuesta correcta era: {correcta}")
                st.session_state.pregunta_actual += 1
                time.sleep(2)
                st.rerun()
        else:
            st.balloons()
            st.success(f"🎉 ¡Juego terminado! Puntaje: {st.session_state.puntaje} de {len(preguntas)}")
            st.session_state.en_juego = False
