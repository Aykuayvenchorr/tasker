import time
import pandas as pd
import streamlit as st
from utils.helpers import Helpers
from services.service_company import ServiceCompany
from ui.ui_comment import UiComment
from ui.ui_tasks import UiTasks


class UiCompany:
    """Класс работы со структурой Компании"""

    @staticmethod
    def init_page():
        """Начльные настройки страницы Компании"""
        # Проверка корректности попадания на страницу
        if 'company_show_form_edit' not in st.session_state:
            st.warning("👿 Не корректное попадание на данную страницу")
            with st.spinner("🛸 Переход на главную страницу..."):
                time.sleep(1)
            st.switch_page('app.py')

        # Сброс стейтов
        st.session_state.company_show_form_add = False
        st.session_state.company_show_form_edit = False


    @staticmethod
    def render_sidebar():
        """Боковая панель Компании"""
        with st.sidebar:
            st.title(f'👋 Привет, {st.session_state.employee.name}!')
            st.divider()
            st.page_link('app.py',
                         label='На главную',
                         icon=':material/home:')
            st.divider()
            if st.button(label='Добавить',
                         key='company_btn_add',
                         width='stretch',
                         icon=':material/add_task:'):
                st.session_state.company_show_form_add = True
                UiCompany.render_dialog_add()
            if st.button(label='Редактировать',
                         key='company_btn_edit',
                         width='stretch',
                         icon=':material/edit_note:',
                         disabled=not st.session_state.company_btn_form_edit):
                st.session_state.company_show_form_edit = True
                UiCompany.render_dialog_edit()


    @staticmethod
    def render_header():
        """Шапка страницы"""
        st.title('🏛 Компании')
        st.divider()

    @staticmethod
    def render_table():
        switch_actual = st.checkbox(label='Только актуальные Компании',
                            key='company_checkbox',
                            value=True)
        is_df, df = ServiceCompany.get_dataframe(switch_actual)
        if is_df:
            event_company = st.dataframe(df,
                             on_select='rerun',
                             selection_mode='single-row',
                             width='content',
                             column_config={
                                 'ID': st.column_config.NumberColumn(
                                     label='ID',
                                     width='small',
                                     help='Id Компании в БД'
                                 ),
                                 'name': st.column_config.TextColumn(
                                     label='Краткое наименование',
                                     width='medium',
                                     help='Краткое наименование Компании'
                                 ),
                                 'full_name': st.column_config.TextColumn(
                                     label='Полное наименование',
                                     width='large',
                                     help='Полное наименование Компании'
                                 ),
                                 'parent': st.column_config.TextColumn(
                                     label='Головная Компания',
                                     width='large',
                                     help='Головная Компания (если текущая Компания - Дочернее Общество)'
                                 ),
                                 'actual': st.column_config.CheckboxColumn(
                                     label='Актуальность',
                                     width='content',
                                     help='Актуальна ли информация'
                                 ),
                             })
            st.write('')

            # Обработка события выбора компании
            if event_company.selection.rows:
                company_id = df.loc[event_company.selection.rows, 'ID'].item()
                st.session_state.company_selected = ServiceCompany.get_company__id(company_id)
                st.session_state.company_btn_form_edit = True
                
                UiComment.render_comments_block(st.session_state.company_selected)
                UiTasks.render_tasks_block(st.session_state.company_selected)
            else:
                st.session_state.company_selected = None
                st.session_state.company_btn_form_edit = False


    @staticmethod
    @st.dialog(title="Добавление Компании",
               width="large",
               dismissible=False,
               on_dismiss="ignore")
    def render_dialog_add():
        """Диалоговое окно добвления Компании"""
        if st.session_state.company_show_form_add:
            company_names = ServiceCompany.get_company_names()
            if company_names:
                placeholder = st.empty()
                name = st.text_input(label='Краткое наименование компании')
                full_name = st.text_input(label='Полное наименование компании')
                parent = st.selectbox(label="Родительская компания",
                                      options=company_names)
                note = st.text_area(label='Примечание')

                col1_btn, col2_btn, col3_btn = st.columns([1, 1, 7])
                with col1_btn:
                    if st.button("Сохранить", width='stretch'):
                        if not name.strip():
                            placeholder.error("Поле 'Краткое наименование компании' обязательно для заполнения!")
                        elif not full_name.strip():
                            placeholder.error("Поле 'Полное наименование компании' обязательно для заполнения!")
                        else:
                            res, msg = ServiceCompany.db_company_insert(name, full_name, parent, note)
                            placeholder.success(msg) if res else placeholder.error(msg)
                        time.sleep(1)
                        UiCompany.dialog_add_btn_edit()
                        Helpers.form_close('company_show_form_add')
                with col2_btn:
                    if st.button("Отмена", width='stretch'):
                        UiCompany.dialog_add_btn_edit()
                        Helpers.form_close('company_show_form_add')


    @staticmethod
    @st.dialog(title="Редактирование Компании",
               width="large",
               dismissible=False,
               on_dismiss="ignore")
    def render_dialog_edit():
        """Диалоговое окно редактирования Компании"""
        if st.session_state.company_show_form_edit:
            # Предварительная полготовка данных
            company = st.session_state.company_selected
            company_names = ServiceCompany.get_company_names()
            index_parent = 0
            if company:
                if company.parent:
                    company_parent = ServiceCompany.get_company__id(company.parent)
                    index_parent = company_names.index(company_parent.name)
                placeholder = st.empty()
                name = st.text_input('Краткое наименование компании', value=company.name)
                full_name = st.text_input(label='Полное наименование компании', value=company.full_name)
                parent = st.selectbox("Родительская компания", company_names, index=index_parent)
                contacts = st.text_area("Контактные данные", value=company.contacts)
                note = st.text_area("Примечание", value=company.note)
                actual = st.checkbox("Актуальность", value=company.actual)
                logo = st.text_input('Путь к логотипу', value=company.logo)

                col1_btn, col2_btn, col3_btn = st.columns([1, 1, 7])
                with col1_btn:
                    if st.button("Сохранить", width='stretch'):
                        if not name.strip():
                            placeholder.error("Поле 'Краткое наименование компании' обязательно для заполнения!")
                        elif not full_name.strip():
                            placeholder.error("Поле 'Полное наименование компании' обязательно для заполнения!")
                        else:
                            res, msg = ServiceCompany.db_company_update(company.id, name, full_name, parent, contacts, note, actual, logo)
                            placeholder.success(msg) if res else placeholder.error(msg)
                        time.sleep(1)
                        UiCompany.dialog_add_btn_edit()
                        Helpers.form_close('company_show_form_edit')
                with col2_btn:
                    if st.button("Отмена", width='stretch'):
                        UiCompany.dialog_add_btn_edit()
                        Helpers.form_close('company_show_form_edit')
            else:
                UiCompany.dialog_add_btn_edit()
                Helpers.form_close('company_show_form_edit')


    @staticmethod
    def dialog_add_btn_edit():
        """Костыль для того, что бы кнопка редактирвоания Компании не жила собственной жизнью"""
        if st.session_state.company_selected:
            st.session_state.company_btn_form_edit = False
        else:
            st.session_state.company_btn_form_edit = True