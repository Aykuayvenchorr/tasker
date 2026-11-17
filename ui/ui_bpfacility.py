import time
import pandas as pd
import streamlit as st
from utils.helpers import Helpers
from services.service_bpfacility import ServiceBPFacility
from services.service_project import ServiceProject


class UiBPFacility:
    """Класс работы со структурой Объекты из Бизнес-плана"""

    @staticmethod
    def init_page():
        """Начальные настройки страницы Объекты из Бизнес-плана"""
        # Проверка корректности попадания на страницу
        if 'bpfacility_show_form_edit' not in st.session_state:
            st.warning("👿 Не корректное попадание на данную страницу")
            with st.spinner("🛸 Переход на главную страницу..."):
                time.sleep(1)
            st.switch_page('app.py')

        # Сброс стейтов
        st.session_state.bpfacility_show_form_add = False
        st.session_state.bpfacility_show_form_edit = False


    @staticmethod
    def render_sidebar():
        """Боковая панель Объекты из Бизнес-плана"""
        with st.sidebar:
            st.title(f'👋 Привет, {st.session_state.employee.name}!')
            st.divider()
            st.page_link('app.py',
                         label='На главную',
                         icon=':material/home:')
            st.page_link('pages/pg_busplan.py', 
                         label='Бизнес-планы', 
                         icon=':material/cases:')
            st.divider()
            if st.button(label='Добавить',
                         key='bpfacility_btn_add',
                         width='stretch',
                         icon=':material/add_task:'):
                st.session_state.bpfacility_show_form_add = True
                UiBPFacility.render_dialog_add()
            if st.button(label='Редактировать',
                         key='bpfacility_btn_edit',
                         width='stretch',
                         icon=':material/edit_note:',
                         disabled= not st.session_state.bpfacility_btn_form_edit):
                st.session_state.bpfacility_show_form_edit = True
                UiBPFacility.render_dialog_edit()


    @staticmethod
    def render_header():
        """Шапка страницы"""
        st.title('🛒 Объекты из Бизнес-плана')
        st.divider()

    @staticmethod
    def render_table():
        switch_actual = st.checkbox(label='Только актуальные Объекты из Бизнес-плана',
                            key='bpfacility__checkbox',
                            value=True)
        project_names = ServiceProject.get_project_names()
        project = st.selectbox("Проекты", project_names, key="project_bpfacility")
        is_df, df = ServiceBPFacility.get_dataframe(switch_actual, project)
        if is_df:
            event_bpfacility = st.dataframe(df,
                             on_select='rerun',
                             selection_mode='single-row',
                             width='content',
                             column_config={
                                 'ID': st.column_config.NumberColumn(
                                     label='ID',
                                     width='small',
                                     help='Id Объекта из Бизнес-плана в БД'
                                 ),
                                 'name': st.column_config.TextColumn(
                                     label='Наименование',
                                     width='content',
                                     help='Наименование Объекта из Бизнес-плана'
                                 ),
                                 'project': st.column_config.TextColumn(
                                     label='Проект',
                                     width='content',
                                     help='Проект'
                                 ),
                                 'count': st.column_config.TextColumn(
                                     label='Количество',
                                     width='content',
                                     help='Количество'
                                 ),
                                 'length': st.column_config.TextColumn(
                                     label='Длина',
                                     width='content',
                                     help='Длина'
                                 ),
                                 'square': st.column_config.TextColumn(
                                     label='Площадь',
                                     width='content',
                                     help='Площадь'
                                 ),
                                 'actual': st.column_config.CheckboxColumn(
                                     label='Актуальность',
                                     width='content',
                                     help='Актуальна ли информация'
                                 ),
                             })
            st.write('')

            # Обработка события выбора компании
            if event_bpfacility.selection.rows:
                bpfacility_id = df.loc[event_bpfacility.selection.rows, 'ID'].item()
                st.session_state.bpfacility_selected = ServiceBPFacility.get_bpfacility__id(bpfacility_id)
                st.session_state.bpfacility_btn_form_edit = True
                
                # UiComment.render_comments_block(st.session_state.company_selected)
                # UiTasks.render_tasks_block(st.session_state.company_selected)
            else:
                st.session_state.bpfacility_selected = None
                st.session_state.bpfacility_btn_form_edit = False


    @staticmethod
    @st.dialog(title="Добавление Объекта из Бизнес-плана",
               width="large",
               dismissible=False,
               on_dismiss="ignore")
    def render_dialog_add():
        """Диалоговое окно добавления Объекта из Бизнес-плана"""
        if st.session_state.bpfacility_show_form_add:
            placeholder = st.empty()
            name = st.text_input(label='Наименование Объекта из Бизнес-плана')
            project_names = ServiceProject.get_project_names()
            project = st.selectbox(label='Проект', options=project_names)
            count = st.number_input(label='Количество')
            length = st.number_input(label='Длина')
            square = st.number_input(label='Площадь')

            col1_btn, col2_btn, col3_btn = st.columns([1, 1, 7])
            with col1_btn:
                if st.button("Сохранить", width='stretch'):
                    if not name.strip():
                        placeholder.error("Поле 'Наименование Объекта из Бизнес-плана' обязательно для заполнения!")
                    else:
                        res, msg = ServiceBPFacility.db_bpfacility_insert(name, project, count, length, square)
                        placeholder.success(msg) if res else placeholder.error(msg)
                    time.sleep(1)
                    UiBPFacility.dialog_add_btn_edit()
                    Helpers.form_close('bpfacility_show_form_add')
            with col2_btn:
                if st.button("Отмена", width='stretch'):
                    UiBPFacility.dialog_add_btn_edit()
                    Helpers.form_close('bpfacility_show_form_add')


    @staticmethod
    @st.dialog(title="Редактирование Объекта из Бизнес-плана",
               width="large",
               dismissible=False,
               on_dismiss="ignore")
    def render_dialog_edit():
        """Диалоговое окно редактирования Объекта из Бизнес-плана"""
        if st.session_state.bpfacility_show_form_edit:
            # Предварительная полготовка данных
            bpfacility = st.session_state.bpfacility_selected
            if bpfacility:
                placeholder = st.empty()
                name = st.text_input('Наименование Объекта из Бизнес-плана', value=bpfacility.name)
                
                projects_names = ServiceProject.get_project_names()
                project = ServiceProject.get_project__id(bpfacility.project)
                index_project = projects_names.index(project.name)
                project = st.selectbox('Проект', projects_names, index=index_project)
                
                count = st.number_input('Количество', value=bpfacility.count)
                length = st.number_input('Длина', value=bpfacility.length)
                square = st.number_input('Площадь', value=bpfacility.square)
                note = st.text_area("Примечание", value=bpfacility.note)
                actual = st.checkbox("Актуальность", value=bpfacility.actual)
                col1_btn, col2_btn, col3_btn = st.columns([1, 1, 7])
                with col1_btn:
                    if st.button("Сохранить", width='stretch'):
                        if not name.strip():
                            placeholder.error("Поле 'Наименование Объекта из Бизнес-плана обязательно для заполнения!")
                        else:
                            res, msg = ServiceBPFacility.db_bpfacility_update(bpfacility.id, name, project, count, length, square, note, actual)
                            placeholder.success(msg) if res else placeholder.error(msg)
                        time.sleep(1)
                        UiBPFacility.dialog_add_btn_edit()
                        Helpers.form_close('bpfacility_show_form_edit')
                with col2_btn:
                    if st.button("Отмена", width='stretch'):
                        UiBPFacility.dialog_add_btn_edit()
                        Helpers.form_close('bpfacility_show_form_edit')
            else:
                UiBPFacility.dialog_add_btn_edit()
                Helpers.form_close('bpfacility_show_form_edit')


    @staticmethod
    def dialog_add_btn_edit():
        """Костыль для того, что бы кнопка редактирования Объекта из Бизнес-плана не жила собственной жизнью"""
        if st.session_state.bpfacility_selected:
            st.session_state.bpfacility_btn_form_edit = False
        else:
            st.session_state.bpfacility_btn_form_edit = True