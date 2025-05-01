# lecturas_app.py - LecturApp: Modo Juego COMPLETO con búsqueda mejorada, OCR y flujo de juego funcional

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

st.set_page_config(page_title="LecturApp: Modo Juego", page_icon="📚")

QUIZ_DB = "registro_quizzes.json"
PDF_FOLDER = "libros_cifrados"
os.makedirs(PDF_FOLDER, exist_ok=True)

FERNET_KEY = st.secrets["FERNET_KEY"]
SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
cipher = Fernet(FERNET_KEY.encode())
client = OpenAI(api_key=OPENAI_KEY)

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
        "Mitad literales y mitad interpretativas. En español latino. Formato JSON con 'pregunta', 'opciones', 'respuesta_correcta'.\nTexto:\n" + texto[:3000]
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

# --- UI Principal ---
st.title("📚 LecturApp: Modo Juego")

if "quiz" not in st.session_state:
    st.session_state.quiz = {}
    st.session_state.jugador = ""
    st.session_state.pregunta_idx = 0
    st.session_state.puntaje = 0

nombre = st.text_input("Tu nombre para jugar:")
libro = st.text_input("Nombre del libro:")
autor = st.text_input("Autor:")
editorial = st.text_input("Editorial:")
cantidad = st.selectbox("¿Cuántas preguntas quieres?", [30, 40, 50])

if st.button("🎲 Comenzar juego"):
    if not nombre_valido(nombre):
        st.warning("El nombre contiene palabras no permitidas.")
    else:
        st.session_state.jugador = nombre
        clave = f"{libro.strip().lower()}"
        quizzes = cargar_json(QUIZ_DB)

        if clave in quizzes:
            st.session_state.quiz = quizzes[clave]
        else:
            pdf_data = cargar_pdf_cifrado(libro)
            if not pdf_data:
                link = buscar_pdf_google(libro, autor, editorial)
                pdf_data = descargar_pdf(link) if link else None
                if not pdf_data:
                    st.warning("No se encontró PDF. Puedes subirlo tú mismo.")
                    uploaded = st.file_uploader("Sube el PDF del libro", type=["pdf"])
                    if uploaded:
                        pdf_data = uploaded.read()

            if pdf_data:
                cifrar_y_guardar_pdf(libro, pdf_data)
                texto = extraer_texto_pdf(pdf_data)
                preguntas = generar_preguntas_ai(texto, cantidad)
                if preguntas:
                    quizzes[clave] = {
                        "titulo": libro,
                        "autor": autor,
                        "editorial": editorial,
                        "curso": "",
                        "preguntas": preguntas
                    }
                    guardar_json(QUIZ_DB, quizzes)
                    st.session_state.quiz = quizzes[clave]
                else:
                    st.error("No se pudieron generar preguntas desde el contenido del libro.")
            else:
                st.error("No fue posible obtener el contenido del libro para generar preguntas.")

if st.session_state.quiz and st.session_state.jugador:
    preguntas = st.session_state.quiz["preguntas"]
    idx = st.session_state.pregunta_idx

    if idx < len(preguntas):
        p = preguntas[idx]
        st.markdown(f"### Pregunta {idx + 1}: {p['pregunta']}")
        respuesta = st.radio("Opciones:", p['opciones'], key=f"q_{idx}")

        if st.button("Responder", key=f"btn_{idx}"):
            correcta = p['opciones'][p['respuesta_correcta']]
            if respuesta == correcta:
                st.success("¡Correcto!")
                st.session_state.puntaje += 1
            else:
                st.error(f"Incorrecto. La respuesta correcta era: {correcta}")
            st.session_state.pregunta_idx += 1
            st.rerun()
    else:
        st.balloons()
        st.success(f"Juego terminado, {st.session_state.jugador}! Puntaje: {st.session_state.puntaje}/{len(preguntas)}")
        if st.button("Jugar otra vez"):
            st.session_state.quiz = {}
            st.session_state.pregunta_idx = 0
            st.session_state.puntaje = 0
            st.rerun()
