import time
import pandas as pd
import streamlit as st
from utils.helpers import Helpers
from services.service_bpcostitem import ServiceBPCostItem


class UiBPCostItem:
    """Класс работы со структурой Статьи затрат"""

    @staticmethod
    def init_page():
        """Начальные настройки страницы Статьи затрат"""
        # Проверка корректности попадания на страницу
        if 'bpcostitem_show_form_edit' not in st.session_state:
            st.warning("👿 Не корректное попадание на данную страницу")
            with st.spinner("🛸 Переход на главную страницу..."):
                time.sleep(1)
            st.switch_page('app.py')

        # Сброс стейтов
        st.session_state.bpcostitem_show_form_add = False
        st.session_state.bpcostitem_show_form_edit = False


    @staticmethod
    def render_sidebar():
        """Боковая панель Статьи затрат"""
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
                         key='bpcostitem_btn_add',
                         width='stretch',
                         icon=':material/add_task:'):
                st.session_state.bpcostitem_show_form_add = True
                UiBPCostItem.render_dialog_add()
            if st.button(label='Редактировать',
                         key='bpcostitem_btn_edit',
                         width='stretch',
                         icon=':material/edit_note:',
                         disabled=not st.session_state.bpcostitem_btn_form_edit):
                st.session_state.bpcostitem_show_form_edit = True
                UiBPCostItem.render_dialog_edit()


    @staticmethod
    def render_header():
        """Шапка страницы"""
        st.title('🛒 Статьи затрат')
        st.divider()

    @staticmethod
    def render_table():
        switch_actual = st.checkbox(label='Только актуальные Статьи затрат',
                            key='bpcostitem__checkbox',
                            value=True)
        is_df, df = ServiceBPCostItem.get_dataframe(switch_actual)
        if is_df:
            event_bpcostitem = st.dataframe(df,
                             on_select='rerun',
                             selection_mode='single-row',
                             width='content',
                             column_config={
                                 'ID': st.column_config.NumberColumn(
                                     label='ID',
                                     width='small',
                                     help='Id статьи затрат в БД'
                                 ),
                                 'name': st.column_config.TextColumn(
                                     label='Наименование',
                                     width='content',
                                     help='Наименование статьи затрат'
                                 ),
                                 'actual': st.column_config.CheckboxColumn(
                                     label='Актуальность',
                                     width='content',
                                     help='Актуальна ли информация'
                                 ),
                             })
            st.write('')

            # Обработка события выбора компании
            if event_bpcostitem.selection.rows:
                bpcostitem_id = df.loc[event_bpcostitem.selection.rows, 'ID'].item()
                st.session_state.bpcostitem_selected = ServiceBPCostItem.get_bpcostitem__id(bpcostitem_id)
                st.session_state.bpcostitem_btn_form_edit = True
                
                # UiComment.render_comments_block(st.session_state.company_selected)
                # UiTasks.render_tasks_block(st.session_state.company_selected)
            else:
                st.session_state.bpcostitem_selected = None
                st.session_state.bpcostitem_btn_form_edit = False


    @staticmethod
    @st.dialog(title="Добавление Статьи затрат",
               width="large",
               dismissible=False,
               on_dismiss="ignore")
    def render_dialog_add():
        """Диалоговое окно добавления Статьи затрат"""
        if st.session_state.bpcostitem_show_form_add:
            placeholder = st.empty()
            name = st.text_input(label='Наименование статьи затрат')

            col1_btn, col2_btn, col3_btn = st.columns([1, 1, 7])
            with col1_btn:
                if st.button("Сохранить", width='stretch'):
                    if not name.strip():
                        placeholder.error("Поле 'Наименование статьи затрат' обязательно для заполнения!")
                    else:
                        res, msg = ServiceBPCostItem.db_bpcostitem_insert(name)
                        placeholder.success(msg) if res else placeholder.error(msg)
                    time.sleep(1)
                    UiBPCostItem.dialog_add_btn_edit()
                    Helpers.form_close('bpcostitem_show_form_add')
            with col2_btn:
                if st.button("Отмена", width='stretch'):
                    UiBPCostItem.dialog_add_btn_edit()
                    Helpers.form_close('bpcostitem_show_form_add')


    @staticmethod
    @st.dialog(title="Редактирование Статьи затрат",
               width="large",
               dismissible=False,
               on_dismiss="ignore")
    def render_dialog_edit():
        """Диалоговое окно редактирования Статьи затрат"""
        if st.session_state.bpcostitem_show_form_edit:
            # Предварительная полготовка данных
            bpcostitem = st.session_state.bpcostitem_selected
            if bpcostitem:
                placeholder = st.empty()
                name = st.text_input('Наименование статьи затрат', value=bpcostitem.name)
                note = st.text_area("Примечание", value=bpcostitem.note)
                actual = st.checkbox("Актуальность", value=bpcostitem.actual)
                col1_btn, col2_btn, col3_btn = st.columns([1, 1, 7])
                with col1_btn:
                    if st.button("Сохранить", width='stretch'):
                        if not name.strip():
                            placeholder.error("Поле 'Наименование статьи затрат обязательно для заполнения!")
                        else:
                            res, msg = ServiceBPCostItem.db_bpcostitem_update(bpcostitem.id, name, note, actual)
                            placeholder.success(msg) if res else placeholder.error(msg)
                        time.sleep(1)
                        UiBPCostItem.dialog_add_btn_edit()
                        Helpers.form_close('bpcostitem_show_form_edit')
                with col2_btn:
                    if st.button("Отмена", width='stretch'):
                        UiBPCostItem.dialog_add_btn_edit()
                        Helpers.form_close('bpcostitem_show_form_edit')
            else:
                UiBPCostItem.dialog_add_btn_edit()
                Helpers.form_close('bpcostitem_show_form_edit')


    @staticmethod
    def dialog_add_btn_edit():
        """Костыль для того, что бы кнопка редактирования статьи затрат не жила собственной жизнью"""
        if st.session_state.bpcostitem_selected:
            st.session_state.bpcostitem_btn_form_edit = False
        else:
            st.session_state.bpcostitem_btn_form_edit = True