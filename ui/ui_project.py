import time
import datetime
import pandas as pd
import streamlit as st
from utils.helpers import Helpers
from services.service_division import ServiceDivision
from services.service_company import ServiceCompany
from services.service_project import ServiceProject
from services.service_license import ServiceLicense
from ui.ui_comment import UiComment
from ui.ui_tasks import UiTasks


class UiProject:
    """Класс работы со структурой Проекта"""

    @staticmethod
    def init_page():
        """Начльные настройки страницы Проекта"""
        # Проверка корректности попадания на страницу
        if 'project_show_form_edit' not in st.session_state:
            st.warning("👿 Не корректное попадание на данную страницу")
            with st.spinner("🛸 Переход на главную страницу..."):
                time.sleep(1)
            st.switch_page('app.py')

        # Сброс стейтов
        st.session_state.project_show_form_add = False
        st.session_state.project_show_form_edit = False


    @staticmethod
    def render_sidebar():
        """Боковая панель Проекта"""
        with st.sidebar:
            st.title(f'👋 Привет, {st.session_state.employee.name}!')
            st.divider()
            st.page_link('app.py',
                         label='На главную',
                         icon=':material/home:')
            st.divider()
            if st.button(label='Добавить',
                         key='project_btn_add',
                         width='stretch',
                         icon=':material/add_task:'):
                st.session_state.project_show_form_add = True
                UiProject.render_dialog_add()
            if st.button(label='Редактировать',
                         key='project_btn_edit',
                         width='stretch',
                         icon=':material/edit_note:',
                         disabled=not st.session_state.project_btn_form_edit):
                st.session_state.project_show_form_edit = True
                UiProject.render_dialog_edit()


    @staticmethod
    def render_header():
        """Шапка страницы"""
        st.title('📊 Проекты')
        st.divider()

    @staticmethod
    def render_table():
        switch_actual = st.checkbox(label='Только актуальные Проекты',
                            key='project_checkbox',
                            value=True)
        # Если Компания не выбрана - необходимо выбрать компания, отображаются все проекты
        # Если Компания выбрана - список подразделений в соответствии с выбранной компанией, необходимо выбрать подразделение
        # ==========================================================================
        company_names = ServiceCompany.get_company_names()
        company = st.selectbox("Компании", company_names, key="company_proj")
        # company_obj = ServiceCompany.get_companies__names(company)
        
        # division_names = ServiceDivision.get_divisions__companies(company_obj, [])
        division_names = ServiceDivision.get_division_names(company)
        division = st.selectbox("Подразделения", division_names, key="division_proj")

   
        is_df, df = ServiceProject.get_dataframe(switch_actual, division, company)
        if is_df:
            event_project = st.dataframe(df,
                             on_select='rerun',
                             selection_mode='single-row',
                             width='content',
                             column_config={
                                 'ID': st.column_config.NumberColumn(
                                     label='ID',
                                     width='small',
                                     help='Id Проекта в БД'
                                 ),
                                 'name': st.column_config.TextColumn(
                                     label='Наименование',
                                     width='medium',
                                     help='Наименование Проекта'
                                 ),
                                 'division': st.column_config.TextColumn(
                                     label='Подразделение',
                                     width='large',
                                     help='Подразделение'
                                 ),
                                 'licenses': st.column_config.TextColumn(
                                     label='Лицензии',
                                     width='content',
                                     help='Лицензии'
                                 ),
                                 'actual': st.column_config.CheckboxColumn(
                                     label='Актуальность',
                                     width='content',
                                     help='Актуальна ли информация'
                                 ),
                             })
            st.write('')

            # Обработка события выбора лицензии
            if event_project.selection.rows:
                project_id = df.loc[event_project.selection.rows, 'ID'].item()
                st.session_state.project_selected = ServiceProject.get_project__id(project_id)
                st.session_state.project_btn_form_edit = True
                
                UiComment.render_comments_block(st.session_state.project_selected)
                UiTasks.render_tasks_block(st.session_state.project_selected)
            else:
                st.session_state.project_selected = None
                st.session_state.project_btn_form_edit = False


    @staticmethod
    @st.dialog(title="Добавление Проекта",
               width="large",
               dismissible=False,
               on_dismiss="ignore")
    def render_dialog_add():
        """Диалоговое окно добавления Проекта"""
        if st.session_state.project_show_form_add:
            division = None
            placeholder = st.empty()
            name = st.text_input(label='Наименование проекта')
            contacts = st.text_area('Контакты')
            note = st.text_area(label='Примечание')
            company_names = ServiceCompany.get_company_names()
            company = st.selectbox("Компания", company_names)
            if company:
                division_names = ServiceDivision.get_division_names(company)
                division = st.selectbox("Подразделения", division_names)
            license_names = ServiceLicense.get_license_names()
            licenses = st.multiselect('Лицензии', options=license_names)
            col1_btn, col2_btn, col3_btn = st.columns([1, 1, 7])
            with col1_btn:
                if st.button("Сохранить", width='stretch'):
                    if not name.strip():
                        placeholder.error("Поле 'Наименование проекта' обязательно для заполнения!")
                    if not company.strip():
                        placeholder.error("Поле 'Компания' обязательно для заполнения!")
                    if not division.strip():
                        placeholder.error("Поле 'Подразделение' обязательно для заполнения!")
                    else:
                        res, msg = ServiceProject.db_project_insert(name, contacts, note, company, division, licenses)
                        placeholder.success(msg) if res else placeholder.error(msg)
                    time.sleep(1)
                    UiProject.dialog_add_btn_edit()
                    Helpers.form_close('project_show_form_add')
            with col2_btn:
                if st.button("Отмена", width='stretch'):
                    UiProject.dialog_add_btn_edit()
                    Helpers.form_close('project_show_form_add')


    @staticmethod
    @st.dialog(title="Редактирование Проекта",
               width="large",
               dismissible=False,
               on_dismiss="ignore")
    def render_dialog_edit():
        """Диалоговое окно редактирования Проекта"""
        if st.session_state.project_show_form_edit:
            # Предварительная подготовка данных
            project = st.session_state.project_selected
            if project:
                placeholder = st.empty()
                name = st.text_input('Наименование проекта', value=project.name)
                contacts = st.text_area('Контакты', value=project.contacts)
                note = st.text_area("Примечание", value=project.note)
                actual = st.checkbox("Актуальность", value=project.actual)
                company_names = ServiceCompany.get_company_names()
                div = ServiceDivision.get_division__id(project.division)
                cmp = ServiceCompany.get_company__id(div.company)
                index_company = company_names.index(cmp.name)
                company = st.selectbox("Компания", company_names, index=index_company)
                if company:
                    division_names = ServiceDivision.get_division_names(company)
                    index_division_names = division_names.index(div.name)
                    division = st.selectbox("Подразделения", division_names, index=index_division_names)
                license_names = ServiceLicense.get_license_names()
                current_licenses = ServiceLicense.get_licenses_names_by_project_id(project.id)
                
                licenses = st.multiselect('Лицензии', options=license_names, default=current_licenses)
                col1_btn, col2_btn, col3_btn = st.columns([1, 1, 7])
                with col1_btn:
                    if st.button("Сохранить", width='stretch'):
                        if not name.strip():
                            placeholder.error("Поле 'Наименование проекта' обязательно для заполнения!")
                        else:
                            res, msg = ServiceProject.db_project_update(project.id, name, contacts, note, actual, company, division, licenses)
                            placeholder.success(msg) if res else placeholder.error(msg)
                        time.sleep(1)
                        UiProject.dialog_add_btn_edit()
                        Helpers.form_close('project_show_form_edit')
                with col2_btn:
                    if st.button("Отмена", width='stretch'):
                        UiProject.dialog_add_btn_edit()
                        Helpers.form_close('project_show_form_edit')
            else:
                UiProject.dialog_add_btn_edit()
                Helpers.form_close('project_show_form_edit')


    @staticmethod
    def dialog_add_btn_edit():
        """Костыль для того, что бы кнопка редактирования Проекта не жила собственной жизнью"""
        if st.session_state.project_selected:
            st.session_state.project_btn_form_edit = False
        else:
            st.session_state.project_btn_form_edit = True