import streamlit as st
import utils
import time 

st.set_page_config(page_title="Inicio de sesión", page_icon=":lock:", layout="centered", initial_sidebar_state="collapsed")

st.title("Iniciar sesión")
username = st.text_input("Nombre de usuario")
password = st.text_input("Contraseña", type="password")

if st.button("Entrar"):
    if utils.login(username, password):
        st.success("Inicio de sesión exitoso")
        st.session_state.logged_in = True
        st.session_state.username = username
        time.sleep(1.2)
        st.switch_page("pages/dashboard.py")
    else:
        st.error("Nombre de usuario o contraseña incorrectos")