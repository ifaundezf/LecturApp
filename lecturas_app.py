# lecturas_app.py

import streamlit as st
import random
import time
import os
import requests
from dotenv import load_dotenv

# Configurar la app
st.set_page_config(page_title="LecturApp", page_icon="📚")

# --- Variables iniciales ---
load_dotenv()
usuarios = {"catita": "1234", "leito": "5678"}
QUIZIZZ_EMAIL = os.getenv("QUIZIZZ_EMAIL")
QUIZIZZ_PASSWORD = os.getenv("QUIZIZZ_PASSWORD")
API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-small"
API_TOKEN = "TU_TOKEN_AQUI"

headers = {"Authorization": f"Bearer {API_TOKEN}"}

# --- Funciones auxiliares ---

def login_quizizz():
    url = "https://quizizz.com/_api/v1/login"
    payload = {
        "email": QUIZIZZ_EMAIL,
        "password": QUIZIZZ_PASSWORD
    }
    headers_login = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers_login)

    if response.status_code == 200:
        session_data = response.json()
        token = session_data.get("token")
        user_id = session_data.get("user", {}).get("_id")
        return token, user_id
    else:
        st.error("Error al iniciar sesión en Quizizz")
        return None, None

def crear_quizizz(token, user_id, nombre_libro, preguntas):
    url = "https://quizizz.com/_api/main/quiz/create"
    headers_create = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    questions_payload = []
    for idx, pregunta in enumerate(preguntas):
        question = {
            "structure": pregunta,
            "type": "MCQ",
            "options": [
                {"text": "Opción 1", "isCorrect": idx % 4 == 0},
                {"text": "Opción 2", "isCorrect": idx % 4 == 1},
                {"text": "Opción 3", "isCorrect": idx % 4 == 2},
                {"text": "Opción 4", "isCorrect": idx % 4 == 3},
            ],
            "time": 20000
        }
        questions_payload.append(question)

    payload = {
        "name": nombre_libro,
        "questions": questions_payload,
        "createdBy": user_id
    }

    response = requests.post(url, json=payload, headers=headers_create)

    if response.status_code == 200:
        quiz = response.json()
        quiz_id = quiz.get("_id")
        return f"https://quizizz.com/admin/quiz/{quiz_id}"
    else:
        st.error("Error al crear el quiz en Quizizz")
        return None

def mostrar_animacion():
    imagenes = ["assets/lectura_1.png", "assets/lectura_2.png", "assets/lectura_3.png", "assets/lectura_4.png"]
    mensajes = [
        "Pensando en preguntas mágicas...",
        "Consultando sabios libros...",
        "Anotando ideas geniales...",
        "Ya casi está listo tu quiz..."
    ]
    placeholder = st.empty()
    for i in range(4):
        with placeholder.container():
            st.image(imagenes[i % len(imagenes)], width=200)
            st.info(mensajes[i % len(mensajes)])
        time.sleep(3)

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    try:
        result = response.json()
        if isinstance(result, list) and "generated_text" in result[0]:
            return result[0]["generated_text"]
        elif "generated_text" in result:
            return result["generated_text"]
        else:
            return ""
    except Exception as e:
        print("Error al decodificar respuesta:", e)
        return ""

def generar_preguntas(libro, autor, editorial, cantidad):
    preguntas_generadas = []
    intentos = 0
    while len(preguntas_generadas) < cantidad and intentos < cantidad * 3:
        prompt = f"Crea una pregunta única sobre el libro '{libro}' escrito por {autor}, publicado por {editorial}. Que sea relevante para un niño."
        output = query({"inputs": prompt})
        if output:
            pregunta = output.strip()
            if pregunta and pregunta not in preguntas_generadas:
                preguntas_generadas.append(pregunta)
        intentos += 1
    return preguntas_generadas

# --- Inicio de la app ---

if "logueado" not in st.session_state:
    st.session_state.logueado = False

if not st.session_state.logueado:
    st.title("LecturApp")
    st.subheader("Iniciar sesión")
    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if user in usuarios and usuarios[user] == password:
            st.session_state.usuario = user
            st.session_state.logueado = True
            st.success(f"¡Bienvenido {user.capitalize()}!")
        else:
            st.error("Usuario o contraseña incorrectos")
    st.stop()

# --- Formulario de creación de quiz ---

st.header("Crear un nuevo Quizizz")
nombre_libro = st.text_input("Nombre del libro")
autor = st.text_input("Autor del libro")
editorial = st.text_input("Editorial")
cantidad_preguntas = st.selectbox("Cantidad de preguntas", [30, 40, 50])
tiempo_respuesta = st.selectbox("Tiempo para responder (segundos)", [5,10,20,30,60,90,120,240])

if st.button("Crear mi Quizizz"):
    if not nombre_libro:
        st.warning("Por favor, ingresa el nombre del libro.")
        st.stop()

    with st.spinner("Creando tu quiz..."):
        mostrar_animacion()
        preguntas = generar_preguntas(nombre_libro, autor, editorial, cantidad_preguntas)
        token, user_id = login_quizizz()
        if token and user_id:
            link_real = crear_quizizz(token, user_id, nombre_libro, preguntas)

    if link_real:
        st.success(f"¡{st.session_state.usuario.capitalize()}, tu Quizizz de '{nombre_libro}' está listo!")
        st.markdown(f"**Link al juego:** [Ir al Quizizz]({link_real})")

    # Mostrar las preguntas
    with st.expander("Ver preguntas generadas"):
        for idx, preg in enumerate(preguntas, 1):
            st.write(f"{idx}. {preg}")

# Fin del archivo
