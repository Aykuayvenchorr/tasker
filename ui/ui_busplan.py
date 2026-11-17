import time
import pandas as pd
import streamlit as st
from utils.helpers import Helpers
from services.service_busplan import ServiceBusplan
from services.service_project import ServiceProject
from ui.ui_busplanstr import UiBusplanStr
# from ui.ui_busplanstr_1 import UiBusplanStr


class UiBusplan:
    """Класс работы со структурой Бизнес-плана"""

    @staticmethod
    def init_page():
        """Начльные настройки страницы Бизнес-плана"""
        # Проверка корректности попадания на страницу
        if 'busplan_show_form_edit' not in st.session_state:
            st.warning("👿 Не корректное попадание на данную страницу")
            with st.spinner("🛸 Переход на главную страницу..."):
                time.sleep(1)
            st.switch_page('app.py')

        # Сброс стейтов
        st.session_state.busplan_show_form_add = False
        st.session_state.busplan_show_form_edit = False


    @staticmethod
    def render_sidebar():
        """Боковая панель Бизнес-плана"""
        with st.sidebar:
            st.title(f'👋 Привет, {st.session_state.employee.name}!')
            st.divider()
            st.page_link('app.py',
                         label='На главную',
                         icon=':material/home:')
            st.divider()
            if st.button(label='Добавить',
                         key='busplan_btn_add',
                         width='stretch',
                         icon=':material/add_task:'):
                st.session_state.busplan_show_form_add = True
                UiBusplan.render_dialog_add()
            if st.button(label='Редактировать',
                         key='busplan_btn_edit',
                         width='stretch',
                         icon=':material/edit_note:',
                         disabled=not st.session_state.busplan_btn_form_edit):
                st.session_state.busplan_show_form_edit = True
                UiBusplan.render_dialog_edit()
            if st.button(label="Добавить строку БП",
                         key="busplanstr_btn_add",
                         width="stretch",
                         icon=":material/add_task:",
                         disabled=not st.session_state.busplan_selected):
                UiBusplanStr.render_dialog_add()

            st.divider()
            st.page_link('pages/pg_project_stage.py',
                         label='Этапы проекта',
                         icon=':material/tactic:')
            st.page_link('pages/pg_bpcostitem.py',
                         label='Статьи затрат',
                         icon=':material/money_range:')
            st.page_link('pages/pg_bpfacility.py',
                         label='Объекты бизнес-плана',
                         icon=':material/factory:')


    @staticmethod
    def render_header():
        """Шапка страницы"""
        st.title('💸 Бизнес-планы')
        st.divider()

    @staticmethod
    def render_table():
        switch_actual = st.checkbox(label='Только актуальные Бизнес-планы',
                            key='busplan_checkbox',
                            value=True)
        project_names = ServiceProject.get_project_names()
        project = st.selectbox("Проекты", project_names, key="project_bp")
        is_df, df = ServiceBusplan.get_dataframe(switch_actual, project)
        if is_df:
            event_busplan = st.dataframe(df,
                             on_select='rerun',
                             selection_mode='single-row',
                             width='content',
                             column_config={
                                 'ID': st.column_config.NumberColumn(
                                     label='ID',
                                     width='small',
                                     help='Id Бизнес-плана в БД'
                                 ),
                                 'name': st.column_config.TextColumn(
                                     label='Наименование',
                                     width='content',
                                     help='Наименование бизнес-плана'
                                 ),
                                 'date': st.column_config.DateColumn(
                                     label='Дата',
                                     width='small',
                                     help='Дата бизнес-плана'
                                 ),
                                 'project': st.column_config.TextColumn(
                                     label='Проект',
                                     width='content',
                                     help='Проект бизнес-плана'
                                 ),
                                 'parent': st.column_config.TextColumn(
                                     label='Головной бизнес-план',
                                     width='large',
                                     help='Головной бизнес-план'
                                 ),
                                 'actual': st.column_config.CheckboxColumn(
                                     label='Актуальность',
                                     width='content',
                                     help='Актуальна ли информация'
                                 ),
                             })
            st.write('')

            # Обработка события выбора компании
            if event_busplan.selection.rows:
                busplan_id = df.loc[event_busplan.selection.rows, 'ID'].item()
                st.session_state.busplan_selected = ServiceBusplan.get_busplan__id(busplan_id)
                st.session_state.busplan_btn_form_edit = True
                if st.button("Сформировать мониторинг"):
                
                    try:
                        monitoring_id = ServiceBusplan.form_monitoring(
                            source_bp_id=busplan_id
                        )
                
                        st.success(
                            f"Мониторинг успешно сформирован. ID: {monitoring_id}"
                        )
                
                        st.rerun()
                
                    except Exception as e:
                        st.error(f"Ошибка формирования мониторинга: {e}")

                st.divider()
                st.subheader(f"Строки бизнес-плана: {st.session_state.busplan_selected.name}")
                UiBusplanStr.render_table(st.session_state.busplan_selected.id)
               

                # UiComment.render_comments_block(st.session_state.company_selected)
                # UiTasks.render_tasks_block(st.session_state.company_selected)
            else:
                st.session_state.busplan_selected = None
                st.session_state.busplan_btn_form_edit = False


    @staticmethod
    @st.dialog(title="Добавление Бизнес-плана",
               width="large",
               dismissible=False,
               on_dismiss="ignore")
    def render_dialog_add():
        """Диалоговое окно добвления Бизнес-плана"""
        if st.session_state.busplan_show_form_add:
            busplan_names = ServiceBusplan.get_busplan_names()
            project_names = ServiceProject.get_project_names()
            if busplan_names:
                placeholder = st.empty()
                name = st.text_input(label='Наименование бизнес-плана')
                date = st.date_input(label='Дата бизнес-плана')
                project = st.selectbox('Проект', options=project_names)
                if project:
                    busplan_names = ServiceBusplan.get_busplan_names_by_project(project)
                parent = st.selectbox(label="Головной бизнес-план", options=busplan_names)
                note = st.text_area(label='Примечание')
                doc = st.text_input(label='📂 Документы', help='Место размещения документов')

                col1_btn, col2_btn, col3_btn = st.columns([1, 1, 7])
                with col1_btn:
                    if st.button("Сохранить", width='stretch'):
                        if not name.strip():
                            placeholder.error("Поле 'Наименование бизнес-плана' обязательно для заполнения!")
                        elif not date:
                            placeholder.error("Поле 'Дата бизнес-плана' обязательна для заполнения!")
                        elif not project:
                            placeholder.error("Поле 'Проект' обязательно для заполнения!")
                        else:
                            res, msg = ServiceBusplan.db_busplan_insert(parent, name, date, project, note, doc)
                            placeholder.success(msg) if res else placeholder.error(msg)
                        time.sleep(1)
                        UiBusplan.dialog_add_btn_edit()
                        Helpers.form_close('busplan_show_form_add')
                with col2_btn:
                    if st.button("Отмена", width='stretch'):
                        UiBusplan.dialog_add_btn_edit()
                        Helpers.form_close('busplan_show_form_add')


    @staticmethod
    @st.dialog(title="Редактирование Бизнес-плана",
               width="large",
               dismissible=False,
               on_dismiss="ignore")
    def render_dialog_edit():
        """Диалоговое окно редактирования Бизнес-плана"""
        if st.session_state.busplan_show_form_edit:
            # Предварительная полготовка данных
            busplan = st.session_state.busplan_selected
            # busplan_names = ServiceBusplan.get_busplan_names()
            index_parent = 0
            if busplan:
                placeholder = st.empty()
                name = st.text_input('Наименование Бизнес-плана', value=busplan.name)
                date = st.date_input('Дата Бизнес-плана', value=busplan.date)
                projects_names = ServiceProject.get_project_names()
                project_name = ServiceProject.get_project_name(busplan.project)
                index_project_names = projects_names.index(project_name)              
                project = st.selectbox("Проект", options=projects_names, index=index_project_names)
                busplan_names = ServiceBusplan.get_busplan_names_by_project(project)
                if project != project_name:
                    parent = st.selectbox("Головной бизнес-план", busplan_names, index=index_parent)
                else:
                    if busplan.parent:
                        busplan_parent = ServiceBusplan.get_busplan__id(busplan.parent)
                        index_parent = busplan_names.index(busplan_parent.name)
                    parent = st.selectbox("Головной бизнес-план", busplan_names, index=index_parent)
                
                note = st.text_area("Примечание", value=busplan.note)
                doc = st.text_input(label='📂 Документы', value=busplan.doc, help='Место размещения документов')
                actual = st.checkbox("Актуальность", value=busplan.actual)
                col1_btn, col2_btn, col3_btn = st.columns([1, 1, 7])
                with col1_btn:
                    if st.button("Сохранить", width='stretch'):
                        if not name.strip():
                            placeholder.error("Поле 'Наименование Бизнес-плана' обязательно для заполнения!")
                        elif not date:
                            placeholder.error("Поле 'Дата бизнес-плана' обязательна для заполнения!")
                        elif not project:
                            placeholder.error("Поле 'Проект' обязательно для заполнения!")
                        else:
                            res, msg = ServiceBusplan.db_busplan_update(parent, busplan.id, name, date, project, note, doc, actual)
                            placeholder.success(msg) if res else placeholder.error(msg)
                        time.sleep(1)
                        UiBusplan.dialog_add_btn_edit()
                        Helpers.form_close('busplan_show_form_edit')
                with col2_btn:
                    if st.button("Отмена", width='stretch'):
                        UiBusplan.dialog_add_btn_edit()
                        Helpers.form_close('busplan_show_form_edit')
            else:
                UiBusplan.dialog_add_btn_edit()
                Helpers.form_close('busplan_show_form_edit')


    @staticmethod
    def dialog_add_btn_edit():
        """Костыль для того, что бы кнопка редактирования Бизнес-плана не жила собственной жизнью"""
        if st.session_state.busplan_selected:
            st.session_state.busplan_btn_form_edit = False
        else:
            st.session_state.busplan_btn_form_edit = True