import streamlit as st
from models import SessionLocal, Company, Division, Employee, License, Project, Task, TaskImportanceEnum, TaskStatusEnum, engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import text

from auth import setup_auth_env, authenticate_user
from lib.filter_task import filter_task

from utils.helpers import Helpers
from ui.ui_auth import UiAuth
from ui.ui_tasks import UiTasks


# Ссылка на Streamlit
# https://dev-22db318c-8303-4dc3-8be7-46275976903a-streamlit.apps.stage.gazprom-neft.local   - старый
# https://5d272a3f-ab90-4322-905c-3e0826e1cbbb-http.apps-spb.dha.paas.gazprom-neft.local/     - новый


# ======================= Иницилизация session state ========================
Helpers.init_session_state()
Helpers.init_page()

# ============================= Аутентификация ==============================

# Создаём сессию базы данных
session = SessionLocal()
try:
    # Получаем пользователя с id=2
    employee = session.query(Employee).filter_by(id=2).one_or_none()

    if employee is None:
        st.error("Пользователь с id=2 не найден в базе данных")
        st.stop()

    st.session_state.employee = employee
    st.session_state.employee_dict = employee.employee_dict()
    st.session_state.employee_current = employee.employee_dict()

finally:
    session.close()

# ============================ Главная страница =============================
UiTasks.render_tasks_sidebar()
UiTasks.render_tasks()


# Текущая страница
st.session_state.current_page_model = None

with st.popover(label='', icon=':material/filter_alt:'):
    filt = filter_task()

# UiTasks.render_tasks_block_main_page(None)
UiTasks.render_tasks_block_main_page(filt)
