import time
import datetime
import pandas as pd
import streamlit as st
from utils.helpers import Helpers
from services.service_license import ServiceLicense
from services.service_company import ServiceCompany
from ui.ui_comment import UiComment
from ui.ui_tasks import UiTasks


class UiLicense:
    """Класс работы со структурой Лицензии"""

    @staticmethod
    def init_page():
        """Начльные настройки страницы Лицензии"""
        # Проверка корректности попадания на страницу
        if 'license_show_form_edit' not in st.session_state:
            st.warning("👿 Не корректное попадание на данную страницу")
            with st.spinner("🛸 Переход на главную страницу..."):
                time.sleep(1)
            st.switch_page('app.py')

        # Сброс стейтов
        st.session_state.license_show_form_add = False
        st.session_state.license_show_form_edit = False


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
                         key='license_btn_add',
                         width='stretch',
                         icon=':material/add_task:'):
                st.session_state.license_show_form_add = True
                UiLicense.render_dialog_add()
            if st.button(label='Редактировать',
                         key='license_btn_edit',
                         width='stretch',
                         icon=':material/edit_note:',
                         disabled=not st.session_state.license_btn_form_edit):
                st.session_state.license_show_form_edit = True
                UiLicense.render_dialog_edit()


    @staticmethod
    def render_header():
        """Шапка страницы"""
        st.title('📜 Лицензии')
        st.divider()

    @staticmethod
    def render_table():
        switch_actual = st.checkbox(label='Только актуальные Лицензии',
                            key='license_checkbox',
                            value=True)
        # Если Компания не выбрана - необходимо выбрать компания, отображаются все лицензии
        # Если Компания выбрана - список Лицензий в соответствии с выбранной компанией
        # ==========================================================================
        company_names = ServiceCompany.get_company_names()
        company = st.selectbox("Компании", company_names, key="company_lic")

        is_df, df = ServiceLicense.get_dataframe(switch_actual, company)
        if is_df:
            event_license = st.dataframe(df,
                             on_select='rerun',
                             selection_mode='single-row',
                             width='content',
                             column_config={
                                 'ID': st.column_config.NumberColumn(
                                     label='ID',
                                     width='small',
                                     help='Id Лицензии в БД'
                                 ),
                                 'name': st.column_config.TextColumn(
                                     label='Наименование',
                                     width='medium',
                                     help='Наименование Лицензии'
                                 ),
                                 'dt_start': st.column_config.DateColumn(
                                     label='Начало',
                                     width='small',
                                     help='Начало'
                                 ),
                                 'dt_end': st.column_config.DateColumn(
                                     label='Завершение',
                                     width='small',
                                     help='Завершение'
                                 ),
                                 'company': st.column_config.TextColumn(
                                     label='Компания',
                                     width='small',
                                     help='Компания'
                                 ),
                                 'actual': st.column_config.CheckboxColumn(
                                     label='Актуальность',
                                     width='content',
                                     help='Актуальна ли информация'
                                 ),
                             })
            st.write('')

            # Обработка события выбора лицензии
            if event_license.selection.rows:
                license_id = df.loc[event_license.selection.rows, 'ID'].item()
                st.session_state.license_selected = ServiceLicense.get_license__id(license_id)
                st.session_state.license_btn_form_edit = True
                
                UiComment.render_comments_block(st.session_state.license_selected)
                UiTasks.render_tasks_block(st.session_state.license_selected)
            else:
                st.session_state.license_selected = None
                st.session_state.license_btn_form_edit = False


    @staticmethod
    @st.dialog(title="Добавление Лицензии",
               width="large",
               dismissible=False,
               on_dismiss="ignore")
    def render_dialog_add():
        """Диалоговое окно добавления Лицензии"""
        if st.session_state.license_show_form_add:
            placeholder = st.empty()
            company_names = ServiceCompany.get_company_names()
            company = st.selectbox("Компании", company_names, key="company_lic_add")
            name = st.text_input(label='Наименование лицензии')
            col1_date, col2_date = st.columns([1, 1])
            dt_start = col1_date.date_input(label='Дата начала',
                                            format='YYYY-MM-DD',
                                            min_value=datetime.date(1900, 1, 1),
                                            max_value=datetime.date(2200, 1, 1))
            dt_end = col2_date.date_input(label='Дата завершения',
                                          format='YYYY-MM-DD',
                                          min_value=datetime.date(1900, 1, 1),
                                          max_value=datetime.date(2200, 1, 1))
            doc = st.text_input("Расположение файла")
            note = st.text_area(label='Примечание')
            col1_btn, col2_btn, col3_btn = st.columns([1, 1, 7])
            with col1_btn:
                if st.button("Сохранить", width='stretch'):
                    if not name.strip():
                        placeholder.error("Поле 'Наименование лицензии' обязательно для заполнения!")
                    else:
                        res, msg = ServiceLicense.db_license_insert(name, dt_start, dt_end, doc, note, company)
                        placeholder.success(msg) if res else placeholder.error(msg)
                    time.sleep(1)
                    UiLicense.dialog_add_btn_edit()
                    Helpers.form_close('license_show_form_add')
            with col2_btn:
                if st.button("Отмена", width='stretch'):
                    UiLicense.dialog_add_btn_edit()
                    Helpers.form_close('license_show_form_add')


    @staticmethod
    @st.dialog(title="Редактирование Лицензии",
               width="large",
               dismissible=False,
               on_dismiss="ignore")
    def render_dialog_edit():
        """Диалоговое окно редактирования Лицензии"""
        if st.session_state.license_show_form_edit:
            # Предварительная подготовка данных
            license = st.session_state.license_selected
            if license:
                placeholder = st.empty()
                company_names = ServiceCompany.get_company_names()
                cmp = ServiceCompany.get_company__id(license.company)
                index_company = company_names.index(cmp.name)
                company = st.selectbox("Компании", company_names, index=index_company)
                name = st.text_input('Наименование лицензии', value=license.name)
                col1_date, col2_date = st.columns([1, 1])
                dt_start = col1_date.date_input(label='Выдана',
                                                format='YYYY-MM-DD',
                                                min_value=datetime.date(1940, 1, 1),
                                                max_value=datetime.date(2200, 1, 1),
                                                value=license.dt_start)
                dt_end = col2_date.date_input(label='Завершается',
                                              format='YYYY-MM-DD',
                                              min_value=datetime.date(1900, 1, 1),
                                              max_value=datetime.date(2200, 1, 1),
                                              value=license.dt_end)
                doc = st.text_input("Расположение файла", value=license.doc)
                note = st.text_area("Примечание", value=license.note)
                actual = st.checkbox("Актуальность", value=license.actual)

                col1_btn, col2_btn, col3_btn = st.columns([1, 1, 7])
                with col1_btn:
                    if st.button("Сохранить", width='stretch'):
                        if not name.strip():
                            placeholder.error("Поле 'Наименование лицензии' обязательно для заполнения!")
                        else:
                            res, msg = ServiceLicense.db_license_update(license.id, name, dt_start, dt_end, doc, note, actual, company)
                            placeholder.success(msg) if res else placeholder.error(msg)
                        time.sleep(1)
                        UiLicense.dialog_add_btn_edit()
                        Helpers.form_close('license_show_form_edit')
                with col2_btn:
                    if st.button("Отмена", width='stretch'):
                        UiLicense.dialog_add_btn_edit()
                        Helpers.form_close('license_show_form_edit')
            else:
                UiLicense.dialog_add_btn_edit()
                Helpers.form_close('license_show_form_edit')


    @staticmethod
    def dialog_add_btn_edit():
        """Костыль для того, что бы кнопка редактирования Лицензии не жила собственной жизнью"""
        if st.session_state.license_selected:
            st.session_state.license_btn_form_edit = False
        else:
            st.session_state.license_btn_form_edit = True