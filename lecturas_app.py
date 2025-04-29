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
    url = "https://auth.quizizz.com/oauth/token"
    payload = {
        "grant_type": "password",
        "client_id": "default",
        "username": QUIZIZZ_EMAIL,
        "password": QUIZIZZ_PASSWORD,
        "scope": "openid profile email",
        "audience": "https://quizizz.com/"
    }
    headers_login = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers_login)

    if response.status_code == 200:
        session_data = response.json()
        access_token = session_data.get("access_token")
        return access_token
    else:
        st.error(f"Error al iniciar sesión en Quizizz: {response.status_code}")
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

        access_token = login_quizizz()

        link_real = None  # Inicializamos para evitar NameError

        if access_token:
            preguntas = generar_preguntas(nombre_libro, autor, editorial, cantidad_preguntas)

            # Simulación por ahora (hasta automatizar 100%)
            link_real = f"https://quizizz.com/join/{random.randint(100000,999999)}"
            pin_real = random.randint(100000,999999)

            st.success(f"¡{st.session_state.usuario.capitalize()}, tu Quizizz de '{nombre_libro}' está listo!")

            st.markdown(f"**Link al juego:** [Ir al Quizizz]({link_real})")
            st.markdown(f"**PIN del juego:** {pin_real}")

            with st.expander("Ver preguntas generadas"):
                for idx, preg in enumerate(preguntas, 1):
                    st.write(f"{idx}. {preg}")

        else:
            st.error("No se pudo crear el quiz porque falló el inicio de sesión en Quizizz.")

# Fin del archivo
