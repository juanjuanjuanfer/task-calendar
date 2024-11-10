import streamlit as st
import utils
from datetime import datetime, timedelta

def show_requests_tab():
    # Obtener tareas pendientes de revisión
    pending_tasks = utils.get_pending_admin_tasks()

    if not pending_tasks:
        st.info("No hay tareas pendientes de revisión")
        return

    # Separar tareas por tipo
    extension_tasks = []
    impossible_tasks = []
    
    for task in pending_tasks:
        if task['estado'] == 'extension_solicitada':
            extension_tasks.append(task)
        elif task['estado'] == 'imposible':
            impossible_tasks.append(task)

    # Mostrar tareas con solicitud de extensión
    if extension_tasks:
        st.header("Solicitudes de Extensión")
        for task in extension_tasks:
            with st.expander(f"🕒 {task['nombre']} - {task['asignado_a']}"):
                # Información básica
                st.write(f"**Descripción:** {task['descripcion']}")
                st.write(f"**Fecha actual:** {task['fecha_hora'].strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Razón de la extensión:** {task['solicitud_extension']['razon']}")
                
                # Columnas para la nueva fecha y acciones
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    new_date = st.date_input(
                        "Nueva fecha",
                        min_value=datetime.now().date(),
                        key=f"date_{task['_id']}"
                    )
                
                with col2:
                    new_time = st.time_input(
                        "Nueva hora",
                        value=task['fecha_hora'].time(),
                        key=f"time_{task['_id']}"
                    )
                
                with col3:
                    if st.button("✅ Aprobar", key=f"approve_{task['_id']}"):
                        if utils.approve_extension(task['_id'], new_date, new_time):
                            st.success("Extensión aprobada")
                            st.rerun()

                reason = st.text_input(
                    "Razón de la denegación:",
                    key=f"deny_reason_{task['_id']}"
                )
                if st.button("❌ Denegar", key=f"deny_{task['_id']}"):
                    if utils.deny_extension(task['_id'], reason):
                        st.success("Extensión denegada")
                        st.rerun()

    # Mostrar tareas marcadas como imposibles
    if impossible_tasks:
        st.header("Tareas Marcadas como Imposibles")
        for task in impossible_tasks:
            with st.expander(f"⚠️ {task['nombre']} - {task['asignado_a']}"):
                # Información básica
                st.write(f"**Descripción:** {task['descripcion']}")
                st.write(f"**Fecha:** {task['fecha_hora'].strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Razón de imposibilidad:** {task.get('razon_imposible', 'No especificada')}")
                
                # Opciones de manejo
                action = st.radio(
                    "Acción a tomar:",
                    ["Modificar tarea", "Eliminar tarea", "Denegar solicitud"],
                    key=f"action_{task['_id']}"
                )
                
                if action == "Modificar tarea":
                    new_name = st.text_input(
                        "Nuevo nombre de la tarea:",
                        value=task['nombre'],
                        key=f"new_name_{task['_id']}"
                    )
                    new_description = st.text_area(
                        "Nueva descripción:",
                        value=task['descripcion'],
                        key=f"new_desc_{task['_id']}"
                    )
                    if st.button("Guardar cambios", key=f"save_{task['_id']}"):
                        if utils.handle_impossible_task(
                            task['_id'],
                            "accept",
                            new_name=new_name,
                            new_description=new_description
                        ):
                            st.success("Tarea modificada exitosamente")
                            st.rerun()
                
                elif action == "Eliminar tarea":
                    if st.button("Confirmar eliminación", key=f"delete_{task['_id']}"):
                        if utils.handle_impossible_task(task['_id'], "accept"):
                            st.success("Tarea eliminada exitosamente")
                            st.rerun()
                
                elif action == "Denegar solicitud":
                    reason = st.text_input(
                        "Razón de la denegación:",
                        key=f"imp_deny_reason_{task['_id']}"
                    )
                    if reason and st.button("Confirmar denegación", key=f"deny_imp_{task['_id']}"):
                        if utils.handle_impossible_task(task['_id'], "deny", reason=reason):
                            st.success("Solicitud denegada")
                            st.rerun()

def show_management_tab():
    st.header("Gestión de Tareas")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_status = st.multiselect(
            "Filtrar por estado",
            ["pendiente", "completada", "extension_solicitada", "imposible"],
            default=["pendiente", "completada"]
        )
    with col2:
        filter_user = st.multiselect(
            "Filtrar por usuario",
            ["Juan", "Jose", "Los dos"],
            default=["Juan", "Jose"]
        )
    with col3:
        date_range = st.date_input(
            "Rango de fechas",
            value=(datetime.now().date(), (datetime.now() + timedelta(days=30)).date()),
            key="date_range"
        )

    # Obtener tareas filtradas
    tasks = utils.get_filtered_tasks(
        estados=filter_status,
        usuarios=filter_user,
        fecha_inicio=date_range[0],
        fecha_fin=date_range[1] if len(date_range) > 1 else date_range[0]
    )

    if not tasks:
        st.info("No hay tareas que coincidan con los filtros seleccionados")
        return

    # Mostrar tareas
    for task in tasks:
        with st.expander(f"{task['nombre']} - {task['asignado_a']} ({task['estado']})"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_name = st.text_input(
                    "Nombre:",
                    value=task['nombre'],
                    key=f"edit_name_{task['_id']}"
                )
                new_description = st.text_area(
                    "Descripción:",
                    value=task['descripcion'],
                    key=f"edit_desc_{task['_id']}"
                )
                new_assigned = st.selectbox(
                    "Asignado a:",
                    ["Juan", "Jose"],
                    index=0 if task['asignado_a'] == "Juan" else 1,
                    key=f"edit_assigned_{task['_id']}"
                )
            
            with col2:
                new_date = st.date_input(
                    "Fecha:",
                    value=task['fecha_hora'].date(),
                    key=f"edit_date_{task['_id']}"
                )
                new_time = st.time_input(
                    "Hora:",
                    value=task['fecha_hora'].time(),
                    key=f"edit_time_{task['_id']}"
                )
                new_status = st.selectbox(
                    "Estado:",
                    ["pendiente", "completada"],
                    index=0 if task['estado'] == "pendiente" else 1,
                    key=f"edit_status_{task['_id']}"
                )

            col3, col4 = st.columns([3, 1])
            with col3:
                if st.button("💾 Guardar cambios", key=f"save_changes_{task['_id']}"):
                    if utils.update_task(
                        task['_id'],
                        new_name,
                        new_description,
                        new_date,
                        new_time,
                        new_assigned,
                        new_status
                    ):
                        st.success("Cambios guardados exitosamente")
                        st.rerun()
            
            with col4:
                if st.button("🗑️ Eliminar", key=f"delete_task_{task['_id']}"):
                    if utils.delete_task(task['_id']):
                        st.success("Tarea eliminada exitosamente")
                        st.rerun()

            if task['comentarios']:
                st.write("**Comentarios:**")
                for comment in task['comentarios']:
                    st.write(f"- {comment['fecha'].strftime('%Y-%m-%d %H:%M')}: {comment['texto']}")

def create_admin_dashboard():
    st.set_page_config(page_title="Administrador de Tareas", page_icon="👨‍💼", layout="wide", initial_sidebar_state="collapsed")
    
    if not st.session_state.get("logged_in"):
        st.write("Por favor inicia sesión")
        if st.button("Iniciar sesión"):
            st.switch_page("login.py")
        st.stop()

    st.title("Panel de Administración de Tareas")

    if st.button("Volver"):
        st.switch_page("pages/dashboard.py")

    # Tabs para separar las secciones
    tab1, tab2 = st.tabs(["📋 Solicitudes", "⚙️ Gestión de Tareas"])
    
    with tab1:
        show_requests_tab()
    
    with tab2:
        show_management_tab()

if __name__ == "__main__":
    create_admin_dashboard()