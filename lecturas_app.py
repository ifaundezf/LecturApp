# lecturas_app.py
import streamlit as st
import random
import os
from datetime import datetime

# --- FUNCIONES AUXILIARES ---

def generar_preguntas(nombre_libro, cantidad):
    base_preguntas = [
        f"¿Quién es el autor de {nombre_libro}?",
        f"¿En qué editorial se publicó {nombre_libro}?",
        f"¿Cuál es el tema principal de {nombre_libro}?",
        f"¿Quién es el personaje principal de {nombre_libro}?",
        f"¿Dónde ocurre la historia de {nombre_libro}?",
        f"¿Qué enseñanza deja {nombre_libro}?",
        f"¿Qué emocione se destaca en {nombre_libro}?",
        f"¿Cómo empieza la historia en {nombre_libro}?",
        f"¿Qué dificultad enfrenta el protagonista en {nombre_libro}?",
        f"¿Cómo termina la historia en {nombre_libro}?",
    ]
    preguntas = []
    for _ in range(cantidad):
        pregunta = random.choice(base_preguntas)
        preguntas.append({
            "pregunta": pregunta,
            "opciones": ["Respuesta 1", "Respuesta 2", "Respuesta 3", "Respuesta 4"],
            "correcta": random.randint(1,4)
        })
    return preguntas


# --- INTERFAZ DE USUARIO ---
st.set_page_config(page_title="Lecturas", page_icon="📚")
st.title("Lecturas - Creador de Kahoots")

# --- LOGIN ---
usuarios = {"catita": "1234", "leito": "5678"}

if "logueado" not in st.session_state:
    st.session_state.logueado = False

if not st.session_state.logueado:
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

# --- FORMULARIO PARA CREAR EL JUEGO ---
st.subheader("Crear un nuevo Kahoot")
nombre_libro = st.text_input("Nombre del libro")
autor = st.text_input("Autor")
editorial = st.text_input("Editorial")
cantidad_preguntas = st.selectbox("Cantidad de preguntas", [30, 40, 50])

if st.button("Crear mi Kahoot"):
    if not nombre_libro:
        st.warning("Debes ingresar el nombre del libro")
        st.stop()
    preguntas = generar_preguntas(nombre_libro, cantidad_preguntas)

    # --- SIMULACION DE CREACION DE KAHOOT ---
    link_falso = f"https://kahoot.it/challenge/{random.randint(100000,999999)}"
    pin_falso = random.randint(100000,999999)

    # --- MENSAJE PERSONALIZADO ---
    st.success(f"\U0001F389 {st.session_state.usuario.capitalize()}, tu Kahoot de '{nombre_libro}' está listo!")

    st.markdown(f"**Link al juego:** [Ir al Kahoot]({link_falso})")
    st.markdown(f"**PIN del juego:** {pin_falso}")
    st.button("Copiar Link", on_click=lambda: st.write(f"Copiado: {link_falso}"))

    # --- MOSTRAR PREGUNTAS GENERADAS ---
    with st.expander("Ver preguntas generadas"):
        for idx, preg in enumerate(preguntas, 1):
            st.write(f"{idx}. {preg['pregunta']}")

# Fin