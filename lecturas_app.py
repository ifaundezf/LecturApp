# lecturas_app.py - LecturApp: Modo Juego

import streamlit as st
import json
import os
import random
import time

# Configuración de página
st.set_page_config(page_title="LecturApp: Modo Juego", page_icon="📚")

# Rutas de archivos
QUIZ_DB = "registro_quizzes.json"
SABIAS_QUE = "sabias_que.json"
ASSETS_PATH = "assets"

# Crear archivos base si no existen
if not os.path.exists(QUIZ_DB):
    with open(QUIZ_DB, "w") as f:
        json.dump({}, f)
if not os.path.exists(SABIAS_QUE):
    with open(SABIAS_QUE, "w") as f:
        json.dump({}, f)

# --- Cargar base de datos ---
def cargar_sabias_que():
    try:
        with open(SABIAS_QUE, encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

# --- Validación de nombres ---
def nombre_valido(nombre):
    palabras_prohibidas = ["malo", "tonto", "fuck", "shit", "puta", "mierda"]
    return not any(p in nombre.lower() for p in palabras_prohibidas)

# --- Inicio ---
st.title("📚 LecturApp: Modo Juego")
st.markdown("Bienvenido a tu espacio de lectura y juegos. ¿Qué quieres hacer?")

opcion = st.radio("Elige una opción:", ["🎮 Crear sala de juego", "👥 Unirse a una sala existente"])

# Sesión inicial
if "sala_codigo" not in st.session_state:
    st.session_state.sala_codigo = ""
    st.session_state.jugador = ""
    st.session_state.curso = ""

# Crear sala
if opcion == "🎮 Crear sala de juego":
    st.subheader("Crear nueva sala de juego")
    nombre = st.text_input("Tu nombre")
    curso = st.selectbox("Selecciona tu curso", ["Tercero Básico", "Cuarto Básico", "Quinto Básico", "Sexto Básico"])

    if st.button("Crear sala"):
        if not nombre_valido(nombre):
            st.warning("Por favor, elige un nombre respetuoso.")
        else:
            codigo = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=5))
            st.session_state.sala_codigo = codigo
            st.session_state.jugador = nombre
            st.session_state.curso = curso
            st.success(f"¡Sala creada! Código de sala: {codigo}")
            st.balloons()

# Unirse a sala
if opcion == "👥 Unirse a una sala existente":
    st.subheader("Unirse a sala existente")
    nombre = st.text_input("Tu nombre")
    codigo = st.text_input("Código de sala")

    if st.button("Unirme"):
        if not nombre_valido(nombre):
            st.warning("Por favor, elige un nombre respetuoso.")
        elif not codigo:
            st.warning("Debes ingresar un código de sala válido.")
        else:
            st.session_state.sala_codigo = codigo
            st.session_state.jugador = nombre
            st.success(f"¡Te has unido a la sala {codigo}!")
            st.balloons()

# Mostrar información si hay una sala activa
if st.session_state.sala_codigo and st.session_state.jugador:
    st.markdown(f"### ✅ Jugador: {st.session_state.jugador}")
    st.markdown(f"### ✅ Sala: {st.session_state.sala_codigo}")
    if st.session_state.curso:
        st.markdown(f"### ✅ Curso: {st.session_state.curso}")
    st.info("(Esta es una vista de prueba. Próximo paso: generar quiz o esperar inicio del juego)")

    st.write("Aquí iría el flujo de espera, datos curiosos, y el botón para jugar solo o esperar.")

    sabias = cargar_sabias_que()
    if st.session_state.curso in sabias:
        st.markdown("---")
        st.markdown("#### ¿Sabías que...?")
        st.success(random.choice(sabias[st.session_state.curso]))

    st.button("🔁 Mostrar otro dato curioso")
