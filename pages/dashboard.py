import streamlit as st
import calendar
import datetime
from datetime import date, datetime, timedelta
import utils

def get_status_color(estado):
    # Asegurarse de que estado sea string
    if not isinstance(estado, str):
        return "⚪"
        
    estados = {
        "pendiente": "🟡",
        "completada": "🟢",
        "imposible": "⭕",
        "extension_solicitada": "🟠"
    }
    return estados.get(estado.lower(), "⚪")

def create_calendar():
    st.set_page_config(page_title="Inicio", page_icon=":smile:", layout="centered", initial_sidebar_state="collapsed")
    if not st.session_state.get("logged_in"):
        st.write("Por favor inicia sesión")
        if st.button("Iniciar sesión"):
            st.switch_page("login.py")
        st.stop()

    st.title("Calendario de Tareas")
    if st.button("recargar"):
        st.rerun()
    
    # Create columns for month/year selection
    col1, col2 = st.columns(2)
    
    # Get current date
    current_date = datetime.now()
    
    # Month selection
    months = list(calendar.month_name)[1:]
    with col1:
        month = st.selectbox(
            "Selecciona el mes",
            months,
            index=current_date.month - 1
        )
    
    # Year selection
    with col2:
        year = st.number_input(
            "Selecciona el año",
            min_value=2000,
            max_value=2100,
            value=current_date.year
        )
    
    # Get month number from name
    month_num = list(calendar.month_name).index(month)
    
    # Get all tasks for the selected month
    month_tasks = utils.get_month_tasks(year, month_num)
    
    # Create a dictionary to store tasks by day
    tasks_by_day = {}
    for task in month_tasks:
        try:
            day = task['fecha_hora'].day
            if day not in tasks_by_day:
                tasks_by_day[day] = []
            tasks_by_day[day].append(task['asignado_a'])
        except (KeyError, AttributeError):
            continue
    
    # Create calendar
    cal = calendar.monthcalendar(year, month_num)
    
    # Display calendar
    st.write("### Calendario")
    
    # Create header with day names
    days = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
    cols = st.columns(7)
    for i, day in enumerate(days):
        cols[i].write(f"**{day}**")
    
    # Display calendar grid
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                # Check if this is today's date
                is_today = (date.today().day == day and 
                          date.today().month == month_num and 
                          date.today().year == year)
                
                # Get users with tasks for this day
                users_with_tasks = tasks_by_day.get(day, [])
                # Remove duplicates and join
                users_text = ", ".join(set(users_with_tasks)) if users_with_tasks else ""
                
                # Display day and users
                if is_today:
                    cols[i].markdown(f"**:blue[{day}]**\n{users_text}")
                else:
                    cols[i].write(f"{day}\n{users_text}")
    
    # Date selection
    selected_day = st.number_input(
        "Selecciona el día",
        min_value=1,
        max_value=31,
        value=min(current_date.day, calendar.monthrange(year, month_num)[1])
    )
    
    # Display selected date
    try:
        selected_date = date(year, month_num, selected_day)
        st.write("Fecha seleccionada:", selected_date.strftime("%Y-%m-%d"))
        st.write("Día de la semana:", selected_date.strftime("%A"))
        
        # Get and display tasks for selected day
        day_tasks = utils.get_day_tasks(year, month_num, selected_day)
        
        # button to add task
        if st.button("Agregar tarea"):
            if st.session_state.username != "rossy":
                st.error("No tienes permisos para agregar tareas")
                st.stop()
            st.switch_page("pages/task.py")
        
        if st.button("Administrar tareas"):
            if st.session_state.username != "rossy":
                st.error("No tienes permisos para administrar tareas")
                st.stop()
            st.switch_page("pages/task_manager.py")
            
        # Display tasks
        if day_tasks:
            st.write("### Tareas del día")
            for task in day_tasks:
                try:
                    with st.expander(f"{task.get('nombre', 'Sin nombre')} - {task.get('asignado_a', 'Sin asignar')} {get_status_color(task.get('estado', ''))}"):
                        # Task details
                        st.write(f"**Descripción:** {task.get('descripcion', 'Sin descripción')}")
                        st.write(f"**Hora:** {task['fecha_hora'].strftime('%H:%M')}")
                        st.write(f"**Estado:** {task.get('estado', 'Sin estado')}")
                        
                        # Time alert
                        time_remaining = task['fecha_hora'] - datetime.now()
                        if time_remaining > timedelta(0) and time_remaining < timedelta(hours=3):
                            st.warning("⚠️ ALERTA: POCO TIEMPO DISPONIBLE")
                        
                        # Action buttons
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            if st.button("✅ Completada", key=f"complete_{task['_id']}"):
                                utils.mark_as_completed(task['_id'])
                                st.rerun()
                                
                        
                        with col2:
                            reason = st.text_input("Razón de la extensión:", key=f"reason_{task['_id']}")
                            if st.button("Enviar solicitud", key=f"send_{task['_id']}"):
                                utils.request_extension(task['_id'], reason)
                                    
                        
                        with col3:
                            reason = st.text_input("Razón:", key=f"imp_reason_{task['_id']}")
                            if st.button("Marcar como imposible", key=f"mark_{task['_id']}"):
                                utils.mark_as_impossible(task['_id'], reason)
                                    
                        
                        with col4:
                            comment = st.text_input("Nuevo comentario:", key=f"comment_{task['_id']}")
                            if st.button("📝 Agregar comentario", key=f"add_comment_{task['_id']}"):
                                utils.add_comment(task['_id'], comment)
                                st.rerun()
                                
                        
                        # Display comments
                        comments = task.get('comentarios', [])
                        if comments:
                            st.write("**Comentarios:**")
                            for comment in comments:
                                try:
                                    st.write(f"- {comment['fecha'].strftime('%Y-%m-%d %H:%M')}: {comment['texto']}")
                                except (KeyError, AttributeError):
                                    continue
                except Exception as e:
                    st.error(f"Error al mostrar tarea: {str(e)}")
        else:
            st.info("No hay tareas para este día")
            
    except ValueError:
        st.error("Fecha inválida")

if __name__ == "__main__":
    create_calendar()