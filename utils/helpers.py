import streamlit as st


class Helpers:
    """Вспомогательный класс с общими методами"""

    @staticmethod
    def init_page():
        """Стартовые настройки страницы"""
        st.set_page_config(
            page_title='Задачник УМЗР',
            page_icon='📝',
            layout='wide',
            initial_sidebar_state='expanded'
        )

    @staticmethod
    def form_close(key):
        st.session_state[key] = False
        st.rerun()

    @staticmethod
    def init_session_state():
        """Инициация начальных стейтов"""
        st.session_state.employee = None
        st.session_state.user_email = st.context.headers.get("X-Auth-Request-Email")
        st.session_state.user = st.context.headers.get("X-Auth-Request-User")
        # Комментарии
        st.session_state.comment_show_form_add = False
        # Задачи
        st.session_state.task_show_form_add = False
        # Компании
        st.session_state.company_selected = None
        st.session_state.company_show_form_add = False
        st.session_state.company_show_form_edit = False
        st.session_state.company_btn_form_edit = True
        # Подразделения
        st.session_state.division_selected = None
        st.session_state.division_show_form_add = False
        st.session_state.division_show_form_edit = False
        st.session_state.division_btn_form_edit = True
        # Лицензии
        st.session_state.license_selected = None
        st.session_state.license_show_form_add = False
        st.session_state.license_show_form_edit = False
        st.session_state.license_btn_form_edit = True
        # Проекты
        st.session_state.project_selected = None
        st.session_state.project_show_form_add = False
        st.session_state.project_show_form_edit = False
        st.session_state.project_btn_form_edit = True
        # Объекты
        st.session_state.facility_selected = None
        st.session_state.facility_show_form_add = False
        st.session_state.facility_show_form_edit = False
        st.session_state.facility_btn_form_edit = True
        st.session_state.ftype_show_form_add = False
        # Сотрудники
        st.session_state.employee_selected = None
        st.session_state.employee_show_form_add = False
        st.session_state.employee_show_form_edit = False
        st.session_state.employee_btn_form_edit = True
        # Бизнес-планы
        st.session_state.busplan_selected = None
        st.session_state.busplan_show_form_add = False
        st.session_state.busplan_show_form_edit = False
        st.session_state.busplan_btn_form_edit = True
        # Строки Бизнес-плана
        st.session_state.busplanstr_show_form_add = False
        # Этапы проекта
        st.session_state.projstage_selected = None
        st.session_state.projstage_show_form_add = False
        st.session_state.projstage_show_form_edit = False
        st.session_state.projstage_btn_form_edit = True
        # Статьи затрат
        st.session_state.bpcostitem_selected = None
        st.session_state.bpcostitem_show_form_add = False
        st.session_state.bpcostitem_show_form_edit = False
        st.session_state.bpcostitem_btn_form_edit = True
        # Объекты из Бизнес-плана
        st.session_state.bpfacility_selected = None
        st.session_state.bpfacility_show_form_add = False
        st.session_state.bpfacility_show_form_edit = False
        st.session_state.bpfacility_btn_form_edit = True
        # Раскрытые задачи перед редактированием
        # st.session_state.expanded_tasks = []

    @staticmethod
    def format_label(obj):
        """Показ только имени объекта"""
        return obj.name

    @staticmethod
    def format_label_list(obj):
        """Показ только имени объекта"""
        return obj[1]

    @staticmethod
    def ierarchy(objects, objects_selected_id, owner_dict, str_ierarchy, str_selected, level, field):        
        for obj in objects:
            if obj.id not in [o for o, _ in str_ierarchy]:
                str_ierarchy.append([obj.id, f'{" ↳"*level} {owner_dict[getattr(obj, field)]}: {obj.name}'])
            if obj.id in objects_selected_id:
                if obj.id not in [o for o, _ in str_selected]:
                    str_selected.append([obj.id, f'{" ↳"*level} {owner_dict[getattr(obj, field)]}: {obj.name}'])
            if len(obj.children) > 0:
                sublevel = level + 1
                Helpers.ierarchy(obj.children, objects_selected_id, owner_dict, str_ierarchy, str_selected, sublevel, field)

        return str_selected, str_ierarchy
                