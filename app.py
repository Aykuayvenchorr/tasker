import streamlit as st
from models import SessionLocal, Company, Division, Employee, License, Project, Task, TaskImportanceEnum, TaskStatusEnum, engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import text
# from my_pages.p001_login import login
# import sreamlit_authenticator as stauth

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

UiAuth.employee_info()
session = SessionLocal()

# ============================ Главная страница =============================
UiTasks.render_tasks_sidebar()
UiTasks.render_tasks()


# Проверка наличия зарегистрированного сотрудника
# ==========================================================================

# st.write(st.user)
# user_email = st.context.headers.get("X-Auth-Request-Email")
# st.write(f"Текущий пользователь: {user_email}")
# st.write(st.context.headers)

# employee = session.query(Employee).filter_by(note=st.session_state.user).one_or_none()

# if not (employee):
#     st.error(f"⛔️ Вас не зарегистрировали в самом приложении ({st.session_state.user})")
#     st.stop()
# else:
#     st.session_state.employee_current = employee.employee_dict()
#     st.session_state.employee = employee
#     st.session_state.employee_dict = employee.employee_dict()



# Текущая страница
st.session_state.current_page_model = None

with st.popover(label='', icon=':material/filter_alt:'):
    filt = filter_task()

UiTasks.render_tasks_block_main_page(filt)
