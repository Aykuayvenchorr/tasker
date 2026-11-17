import time
import pandas as pd
import streamlit as st
from utils.helpers import Helpers
from services.service_project_stage import ServiceProjectStage


class UiProjectStage:
    """Класс работы со структурой Этапы проекта"""

    @staticmethod
    def init_page():
        """Начальные настройки страницы Этапы проекта"""
        # Проверка корректности попадания на страницу
        if 'projstage_show_form_edit' not in st.session_state:
            st.warning("👿 Не корректное попадание на данную страницу")
            with st.spinner("🛸 Переход на главную страницу..."):
                time.sleep(1)
            st.switch_page('app.py')

        # Сброс стейтов
        st.session_state.projstage_show_form_add = False
        st.session_state.projstage_show_form_edit = False


    @staticmethod
    def render_sidebar():
        """Боковая панель Бизнес-плана"""
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
                         key='projstage_btn_add',
                         width='stretch',
                         icon=':material/add_task:'):
                st.session_state.projstage_show_form_add = True
                UiProjectStage.render_dialog_add()
            if st.button(label='Редактировать',
                         key='projstage_btn_edit',
                         width='stretch',
                         icon=':material/edit_note:',
                         disabled=not st.session_state.projstage_btn_form_edit):
                st.session_state.projstage_show_form_edit = True
                UiProjectStage.render_dialog_edit()


    @staticmethod
    def render_header():
        """Шапка страницы"""
        st.title('💸 Этапы проекта')
        st.divider()

    @staticmethod
    def render_table():
        switch_actual = st.checkbox(label='Только актуальные Этапы проекта',
                            key='projstage__checkbox',
                            value=True)
        is_df, df = ServiceProjectStage.get_dataframe(switch_actual)
        if is_df:
            event_projstage = st.dataframe(df,
                             on_select='rerun',
                             selection_mode='single-row',
                             width='content',
                             column_config={
                                 'ID': st.column_config.NumberColumn(
                                     label='ID',
                                     width='small',
                                     help='Id этапа проекта в БД'
                                 ),
                                 'name': st.column_config.TextColumn(
                                     label='Наименование',
                                     width='content',
                                     help='Наименование этапа проекта'
                                 ),
                                 'actual': st.column_config.CheckboxColumn(
                                     label='Актуальность',
                                     width='content',
                                     help='Актуальна ли информация'
                                 ),
                             })
            st.write('')

            # Обработка события выбора компании
            if event_projstage.selection.rows:
                projstage_id = df.loc[event_projstage.selection.rows, 'ID'].item()
                st.session_state.projstage_selected = ServiceProjectStage.get_projstage__id(projstage_id)
                st.session_state.projstage_btn_form_edit = True
                
                # UiComment.render_comments_block(st.session_state.company_selected)
                # UiTasks.render_tasks_block(st.session_state.company_selected)
            else:
                st.session_state.projstage_selected = None
                st.session_state.projstage_btn_form_edit = False


    @staticmethod
    @st.dialog(title="Добавление Этапа проекта",
               width="large",
               dismissible=False,
               on_dismiss="ignore")
    def render_dialog_add():
        """Диалоговое окно добавления Этапа проекта"""
        if st.session_state.projstage_show_form_add:
            placeholder = st.empty()
            name = st.text_input(label='Наименование этапа проекта')

            col1_btn, col2_btn, col3_btn = st.columns([1, 1, 7])
            with col1_btn:
                if st.button("Сохранить", width='stretch'):
                    if not name.strip():
                        placeholder.error("Поле 'Наименование этапа проекта' обязательно для заполнения!")
                    else:
                        res, msg = ServiceProjectStage.db_projstage_insert(name)
                        placeholder.success(msg) if res else placeholder.error(msg)
                    time.sleep(1)
                    UiProjectStage.dialog_add_btn_edit()
                    Helpers.form_close('projstage_show_form_add')
            with col2_btn:
                if st.button("Отмена", width='stretch'):
                    UiProjectStage.dialog_add_btn_edit()
                    Helpers.form_close('projstage_show_form_add')


    @staticmethod
    @st.dialog(title="Редактирование Этапа проекта",
               width="large",
               dismissible=False,
               on_dismiss="ignore")
    def render_dialog_edit():
        """Диалоговое окно редактирования Этапа проекта"""
        if st.session_state.projstage_show_form_edit:
            # Предварительная полготовка данных
            projstage = st.session_state.projstage_selected
            if projstage:
                placeholder = st.empty()
                name = st.text_input('Наименование этапа проекта', value=projstage.name)
                note = st.text_area("Примечание", value=projstage.note)
                actual = st.checkbox("Актуальность", value=projstage.actual)
                col1_btn, col2_btn, col3_btn = st.columns([1, 1, 7])
                with col1_btn:
                    if st.button("Сохранить", width='stretch'):
                        if not name.strip():
                            placeholder.error("Поле 'Наименование этапа проекта' обязательно для заполнения!")
                        else:
                            res, msg = ServiceProjectStage.db_projstage_update(projstage.id, name, note, actual)
                            placeholder.success(msg) if res else placeholder.error(msg)
                        time.sleep(1)
                        UiProjectStage.dialog_add_btn_edit()
                        Helpers.form_close('projstage_show_form_edit')
                with col2_btn:
                    if st.button("Отмена", width='stretch'):
                        UiProjectStage.dialog_add_btn_edit()
                        Helpers.form_close('projstage_show_form_edit')
            else:
                UiProjectStage.dialog_add_btn_edit()
                Helpers.form_close('projstage_show_form_edit')


    @staticmethod
    def dialog_add_btn_edit():
        """Костыль для того, что бы кнопка редактирования этапа проекта не жила собственной жизнью"""
        if st.session_state.projstage_selected:
            st.session_state.projstage_btn_form_edit = False
        else:
            st.session_state.projstage_btn_form_edit = True