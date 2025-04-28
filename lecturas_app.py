# lecturas_app.py

import streamlit as st
import random
import time
import os
from transformers import pipeline

# Configurar la app
st.set_page_config(page_title="LecturApp", page_icon="📚")

# --- Variables iniciales ---
usuarios = {"catita": "1234", "leito": "5678"}
model_name = "google/flan-t5-small"
generator = pipeline("text2text-generation", model=model_name)

# --- Funciones auxiliares ---

def mostrar_animacion():
    imagenes = ["assets/lectura_1.png", "assets/lectura_2.png", "assets/lectura_3.png", "assets/lectura_4.png"]
    mensajes = [
        "Pensando en preguntas mágicas...",
        "Consultando sabios libros...",
        "Anotando ideas geniales...",
        "Ya casi está listo tu quiz..."
    ]
    for i in range(4):
        st.image(imagenes[i % len(imagenes)], width=200)
        st.info(mensajes[i % len(mensajes)])
        time.sleep(3)

def generar_preguntas(libro, autor, editorial, cantidad):
    preguntas_generadas = []
    intentos = 0
    while len(preguntas_generadas) < cantidad and intentos < cantidad * 2:
        prompt = f"Crea una pregunta única sobre el libro '{libro}' escrito por {autor}, publicado por {editorial}. Que sea relevante para un niño."
        resultado = generator(prompt, max_length=80, num_return_sequences=1)[0]['generated_text']
        pregunta = resultado.strip()
        if pregunta not in preguntas_generadas:
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

st.header("Crear un nuevo Kahoot")
nombre_libro = st.text_input("Nombre del libro")
autor = st.text_input("Autor del libro")
editorial = st.text_input("Editorial")
cantidad_preguntas = st.selectbox("Cantidad de preguntas", [30, 40, 50])
tiempo_respuesta = st.selectbox("Tiempo para responder (segundos)", [5,10,20,30,60,90,120,240])

if st.button("Crear mi Kahoot"):
    if not nombre_libro:
        st.warning("Por favor, ingresa el nombre del libro.")
        st.stop()

    with st.spinner("Creando tu quiz..."):
        mostrar_animacion()
        preguntas = generar_preguntas(nombre_libro, autor, editorial, cantidad_preguntas)

    st.success(f"¡{st.session_state.usuario.capitalize()}, tu Kahoot de '{nombre_libro}' está listo!")

    # Mostrar link simulado y PIN
    link_falso = f"https://kahoot.it/challenge/{random.randint(100000,999999)}"
    pin_falso = random.randint(100000,999999)
    st.markdown(f"**Link al juego:** [Ir al Kahoot]({link_falso})")
    st.markdown(f"**PIN del juego:** {pin_falso}")

    # Mostrar las preguntas
    with st.expander("Ver preguntas generadas"):
        for idx, preg in enumerate(preguntas, 1):
            st.write(f"{idx}. {preg}")

# Fin del archivo
