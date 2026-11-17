import streamlit as st
from services.service_auth import ServiceAuth


class UiAuth:
    """Пользовательский интерфейс - Пользователь/Сотрудник"""

    @staticmethod
    def render_user_info():
        # st.markdown(f"👤 {st.user.preferred_username}, добрый день!")
        # st.session_state.user_email = st.context.headers.get("X-Auth-Request-Email")
        # st.session_state.user = st.context.headers.get("X-Auth-Request-User")
        st.markdown(f"👤 {st.session_state.user_email}, добрый день!")
        # st.markdown(f"{st.session_state.user}")

    @staticmethod
    def render_title_main():
        """Заголовок на главной страние"""
        st.title("Главная страница")
        UiAuth.render_user_info()

    @staticmethod
    def employee_info():
        employee = ServiceAuth.get_empoyee(st.session_state.user)
        if not (employee):
            st.error(f"⛔️ Вас не зарегистрировали в самом приложении")
            print(f'Пользователь {st.session_state.user_email} не зарегистрирован как сотрудник')
            st.stop()
        else:
            st.session_state.employee = employee
            st.session_state.employee_dict = employee.employee_dict()
            st.session_state.employee_current = employee.employee_dict()

    @staticmethod
    def logout():
        st.logout()