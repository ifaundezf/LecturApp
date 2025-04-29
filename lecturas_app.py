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

def cargar_quizzes():
    try:
        with open(QUIZ_DB, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except:
        return {}

def guardar_quizzes(data):
    with open(QUIZ_DB, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- Generar preguntas dummy (placeholder) ---
def generar_preguntas_dummy(libro, cantidad):
    preguntas = []
    for i in range(int(cantidad)):
        pregunta = {
            "pregunta": f"¿Qué ocurrió en la página {i+1} del libro '{libro}'?",
            "opciones": [
                f"Opción A{i+1}", f"Opción B{i+1}", f"Opción C{i+1}", f"Opción D{i+1}"
            ],
            "respuesta_correcta": random.randint(0, 3)
        }
        preguntas.append(pregunta)
    return preguntas

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
    st.session_state.quiz_generado = False

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
            st.session_state.quiz_generado = False
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
            st.session_state.quiz_generado = False
            st.success(f"¡Te has unido a la sala {codigo}!")
            st.balloons()

# Mostrar información si hay una sala activa
if st.session_state.sala_codigo and st.session_state.jugador:
    st.markdown(f"### ✅ Jugador: {st.session_state.jugador}")
    st.markdown(f"### ✅ Sala: {st.session_state.sala_codigo}")
    if st.session_state.curso:
        st.markdown(f"### ✅ Curso: {st.session_state.curso}")

    quizzes = cargar_quizzes()
    clave_libro = None

    if opcion == "🎮 Crear sala de juego" and not st.session_state.quiz_generado:
        st.markdown("---")
        st.subheader("📚 Configura tu quiz de lectura")

        libro = st.text_input("Nombre del libro")
        autor = st.text_input("Autor")
        editorial = st.text_input("Editorial")
        cantidad = st.selectbox("¿Cuántas preguntas quieres generar?", [30, 40, 50])
        tiempo = st.selectbox("Tiempo para responder cada pregunta:", [5, 10, 20, 30, 60, 90, 120, 240])

        if libro:
            clave_libro = f"{st.session_state.curso} | {libro.strip().lower()}"

        if clave_libro in quizzes:
            st.info("Ya existe un quiz para este libro.")
            if st.button("📂 Usar quiz existente"):
                st.session_state.quiz_generado = True
                st.success("Quiz cargado desde la base de datos.")
            if st.button("🆕 Crear nuevo quiz (sobrescribir)"):
                preguntas = generar_preguntas_dummy(libro, cantidad)
                quizzes[clave_libro] = {
                    "libro": libro,
                    "autor": autor,
                    "editorial": editorial,
                    "curso": st.session_state.curso,
                    "cantidad": cantidad,
                    "tiempo": tiempo,
                    "preguntas": preguntas
                }
                guardar_quizzes(quizzes)
                st.session_state.quiz_generado = True
                st.success("Nuevo quiz preparado. ¡Preguntas listas para jugar!")
        elif libro and autor and editorial:
            if st.button("🪄 Generar quiz nuevo"):
                preguntas = generar_preguntas_dummy(libro, cantidad)
                quizzes[clave_libro] = {
                    "libro": libro,
                    "autor": autor,
                    "editorial": editorial,
                    "curso": st.session_state.curso,
                    "cantidad": cantidad,
                    "tiempo": tiempo,
                    "preguntas": preguntas
                }
                guardar_quizzes(quizzes)
                st.session_state.quiz_generado = True
                st.success("Quiz creado. ¡Preguntas listas para jugar!")

    sabias = cargar_sabias_que()
    if st.session_state.curso in sabias:
        st.markdown("---")
        st.markdown("#### ¿Sabías que...?")
        st.success(random.choice(sabias[st.session_state.curso]))

    st.button("🔁 Mostrar otro dato curioso")

    # Mostrar inicio de juego si ya se generó el quiz
    if st.session_state.quiz_generado:
        st.markdown("## 🎮 ¡Todo listo para jugar!")
        if st.button("Iniciar juego ahora"):
            st.success("Aquí comenzaría el modo de juego activo... (próximo paso)")
