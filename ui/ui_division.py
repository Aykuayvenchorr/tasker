import time
import pandas as pd
import streamlit as st
from utils.helpers import Helpers
from services.service_division import ServiceDivision
from services.service_company import ServiceCompany
from ui.ui_comment import UiComment
from ui.ui_tasks import UiTasks


class UiDivision:
    """Класс работы со структурой Подразделения"""

    @staticmethod
    def init_page():
        """Начльные настройки страницы Подразделения"""
        # Проверка корректности попадания на страницу
        if 'division_show_form_edit' not in st.session_state:
            st.warning("👿 Не корректное попадание на данную страницу")
            with st.spinner("🛸 Переход на главную страницу..."):
                time.sleep(1)
            st.switch_page('app.py')

        # Сброс стейтов
        st.session_state.division_show_form_add = False
        st.session_state.division_show_form_edit = False

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
                         key='division_btn_add',
                         width='stretch',
                         icon=':material/add_task:'):
                st.session_state.division_show_form_add = True
                UiDivision.render_dialog_add()
            if st.button(label='Редактировать',
                         key='division_btn_edit',
                         width='stretch',
                         icon=':material/edit_note:',
                         disabled=not st.session_state.division_btn_form_edit):
                st.session_state.division_show_form_edit = True
                UiDivision.render_dialog_edit()


    @staticmethod
    def render_header():
        """Шапка страницы"""
        st.title('⚒ Подразделения')
        st.divider()

    @staticmethod
    def render_table():
        switch_actual = st.checkbox(label='Только актуальные Подразделения',
                                    key='division_checkbox',
                                    value=True)
        # Если Компания не выбрана - необходимо выбрать компания, отображаются все подразделения
        # Если Компания выбрана - список Подразделений в соответствии с выбранной компанией
        # ==========================================================================
        company_names = ServiceCompany.get_company_names()
        company = st.selectbox("Компании", company_names, key="company_div")

        is_df, df = ServiceDivision.get_dataframe(switch_actual, company)
        if is_df:
            event_division = st.dataframe(df,
                             on_select='rerun',
                             selection_mode='single-row',
                             width='content',
                             column_config={
                                 'ID': st.column_config.NumberColumn(
                                     label='ID',
                                     width='small',
                                     help='Id Подразделения в БД'
                                 ),
                                 'name': st.column_config.TextColumn(
                                     label='Наименование',
                                     width='medium',
                                     help='Наименование Подразделения'
                                 ),
                                 'abbr': st.column_config.TextColumn(
                                     label='Аббревиатура',
                                     width='small',
                                     help='Аббревиатура'
                                 ),
                                 'parent': st.column_config.TextColumn(
                                     label='Верхнеуровневое подразделение',
                                     width='large',
                                     help='Верхнеуровневое подразделение'
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

            # Обработка события выбора подразделения
            if event_division.selection.rows:
                division_id = df.loc[event_division.selection.rows, 'ID'].item()
                st.session_state.division_selected = ServiceDivision.get_division__id(division_id)
                st.session_state.division_btn_form_edit = True
                
                UiComment.render_comments_block(st.session_state.division_selected)
                UiTasks.render_tasks_block(st.session_state.division_selected)
            else:
                st.session_state.division_selected = None
                st.session_state.division_btn_form_edit = False


    @staticmethod
    @st.dialog(title="Добавление Подразделения",
               width="large",
               dismissible=False,
               on_dismiss="ignore")
    def render_dialog_add():
        """Диалоговое окно добавления Подразделения"""
        if st.session_state.division_show_form_add:
            company_names = ServiceCompany.get_company_names()
            placeholder = st.empty()
            name = st.text_input(label='Наименование подразделения')
            abbr = st.text_input(label='Аббревиатура')
            company = st.selectbox("Компании", company_names, key="company_div_add")
            division_names = ServiceDivision.get_division_names(company)
            parent = st.selectbox(label="Головное подразделение",
                                      options=division_names)
            note = st.text_area(label='Примечание')

            col1_btn, col2_btn, col3_btn = st.columns([1, 1, 7])
            with col1_btn:
                if st.button("Сохранить", width='stretch'):
                    if not name.strip():
                        placeholder.error("Поле 'Наименование подразделения' обязательно для заполнения!")
                    elif not abbr.strip():
                        placeholder.error("Аббревиатура' обязательно для заполнения!")
                    else:
                        res, msg = ServiceDivision.db_division_insert(name, abbr, parent, note, company)
                        placeholder.success(msg) if res else placeholder.error(msg)
                    time.sleep(1)
                    UiDivision.dialog_add_btn_edit()
                    Helpers.form_close('division_show_form_add')
            with col2_btn:
                if st.button("Отмена", width='stretch'):
                    UiDivision.dialog_add_btn_edit()
                    Helpers.form_close('division_show_form_add')


    @staticmethod
    @st.dialog(title="Редактирование Подразделения",
               width="large",
               dismissible=False,
               on_dismiss="ignore")
    def render_dialog_edit():
        """Диалоговое окно редактирования Подразделения"""
        if st.session_state.division_show_form_edit:
            # Предварительная полготовка данных
            company_names = ServiceCompany.get_company_names()
            division = st.session_state.division_selected
            company_name = ServiceDivision.get_division_company_name(division)
            index_company = company_names.index(company_name)
            division_names = ServiceDivision.get_division_names(company_name)
            # division_names = ServiceDivision.get_division_names(st.session_state.company_div)
            index_parent = 0
            if division:
                if division.parent:
                    division_parent = ServiceDivision.get_division__id(division.parent)
                    index_parent = division_names.index(division_parent.name)
                placeholder = st.empty()
                name = st.text_input('Наименование подразделения', value=division.name)
                abbr = st.text_input(label='Аббревиатура', value=division.abbr)
                company = st.selectbox("Компании", company_names, index=index_company)
                if company != company_name:
                    division_names = ServiceDivision.get_division_names(company)
                    index_parent = 0
                parent = st.selectbox("Головное подразделение", division_names, index=index_parent)

                print('parent', parent)
                
                contacts = st.text_area("Контактные данные", value=division.contacts)
                note = st.text_area("Примечание", value=division.note)
                actual = st.checkbox("Актуальность", value=division.actual)

                col1_btn, col2_btn, col3_btn = st.columns([1, 1, 7])
                with col1_btn:
                    if st.button("Сохранить", width='stretch'):
                        if not name.strip():
                            placeholder.error("Поле 'Наименование подразделения' обязательно для заполнения!")
                        elif not abbr.strip():
                            placeholder.error("Поле 'Аббревиатура' обязательно для заполнения!")
                        else:
                            res, msg = ServiceDivision.db_division_update(division.id, name, abbr, parent, contacts, note, actual, company)
                            placeholder.success(msg) if res else placeholder.error(msg)
                        time.sleep(1)
                        UiDivision.dialog_add_btn_edit()
                        Helpers.form_close('division_show_form_edit')
                with col2_btn:
                    if st.button("Отмена", width='stretch'):
                        UiDivision.dialog_add_btn_edit()
                        Helpers.form_close('division_show_form_edit')
            else:
                UiDivision.dialog_add_btn_edit()
                Helpers.form_close('division_show_form_edit')


    @staticmethod
    def dialog_add_btn_edit():
        """Костыль для того, что бы кнопка редактирования Подразделения не жила собственной жизнью"""
        if st.session_state.division_selected:
            st.session_state.division_btn_form_edit = False
        else:
            st.session_state.division_btn_form_edit = True