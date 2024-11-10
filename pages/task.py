import streamlit as st
import utils

st.set_page_config(page_title="Tareas", page_icon="📝", layout="wide", initial_sidebar_state="collapsed")

if not st.session_state.get("logged_in"):
    st.write("Por favor inicia sesión")
    if st.button("Iniciar sesión"):
        st.switch_page("login.py")
    st.stop()


st.title("Nueva Tarea")
if st.button("Volver"):
    st.switch_page("pages/dashboard.py")
if st.button("Agregar otra tarea"):
    st.switch_page("pages/task.py")
col1, col2, col3 = st.columns(3)
with col1:
    task_name = st.text_input("Nombre de la tarea")
    task_description = st.text_area("Descripción de la tarea")

with col2:
    task_date = st.date_input("Fecha de la tarea")
    task_time = st.time_input("Hora de la tarea")

with col3:
    assigned_to = st.selectbox("Asignado a", ["Juan", "Jose", "Los dos"])
    if st.button("Agregar tarea"):
        utils.add_task(task_name, task_description, task_date, task_time, assigned_to)
        st.success("Tarea agregada")
        
