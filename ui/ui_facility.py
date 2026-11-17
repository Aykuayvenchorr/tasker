import time
import pandas as pd
import streamlit as st
from utils.helpers import Helpers
from services.service_division import ServiceDivision
from services.service_company import ServiceCompany
from services.service_facility import ServiceFacility
from services.service_license import ServiceLicense
from ui.ui_comment import UiComment
from ui.ui_tasks import UiTasks


class UiFacility:
    """Класс работы со структурой Объекта"""

    @staticmethod
    def init_page():
        """Начльные настройки страницы ПодраОбъектазделения"""
        # Проверка корректности попадания на страницу
        if 'facility_show_form_edit' not in st.session_state:
            st.warning("👿 Не корректное попадание на данную страницу")
            with st.spinner("🛸 Переход на главную страницу..."):
                time.sleep(1)
            st.switch_page('app.py')

        # Сброс стейтов
        st.session_state.facility_show_form_add = False
        st.session_state.facility_show_form_edit = False

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
                         key='facility_btn_add',
                         width='stretch',
                         icon=':material/add_task:'):
                st.session_state.facility_show_form_add = True
                UiFacility.render_dialog_add()
            if st.button(label='Редактировать',
                         key='facility_btn_edit',
                         width='stretch',
                         icon=':material/edit_note:',
                         disabled=not st.session_state.facility_btn_form_edit):
                st.session_state.facility_show_form_edit = True
                UiFacility.render_dialog_edit()
            st.divider()
            if st.button(label='Добавить тип объекта',
                         key='ftype_btn_add',
                         width='stretch',
                         icon=':material/add_task:'):
                st.session_state.ftype_show_form_add = True
                UiFacility.render_dialog_add_ftype()


    @staticmethod
    def render_header():
        """Шапка страницы"""
        st.title('🏗️ Объекты')
        st.divider()

    @staticmethod
    def render_table():
        switch_actual = st.checkbox(label='Только актуальные Объекты',
                                    key='facility_checkbox',
                                    value=True)
        # Если Лицензия не выбрана - необходимо выбрать лицензию, отображаются все объекты
        # Если Лицензия выбрана - список Объектов в соответствии с выбранной лицензией
        # ==========================================================================
        license_names = ServiceLicense.get_license_names()
        license = st.selectbox("Лицензии", license_names, key="license_fc")

        is_df, df = ServiceFacility.get_dataframe(switch_actual, license)
        if is_df:
            event_facility = st.dataframe(df,
                             on_select='rerun',
                             selection_mode='single-row',
                             width='content',
                             column_config={
                                 'ID': st.column_config.NumberColumn(
                                     label='ID',
                                     width='small',
                                     help='Id Объекта в БД'
                                 ),
                                 'name': st.column_config.TextColumn(
                                     label='Наименование',
                                     width='medium',
                                     help='Наименование Объекта'
                                 ),
                                 'ftype': st.column_config.TextColumn(
                                     label='Тип объекта',
                                     width='content',
                                     help='Тип объекта'
                                 ),
                                 'parent': st.column_config.TextColumn(
                                     label='Верхнеуровневый объект',
                                     width='large',
                                     help='Верхнеуровневый объект'
                                 ),
                                 'license': st.column_config.TextColumn(
                                     label='Лицензия',
                                     width='content',
                                     help='Лицензия'
                                 ),
                                 'actual': st.column_config.CheckboxColumn(
                                     label='Актуальность',
                                     width='content',
                                     help='Актуальна ли информация'
                                 ),
                             })
            st.write('')

            # Обработка события выбора Объекта
            if event_facility.selection.rows:
                facility_id = df.loc[event_facility.selection.rows, 'ID'].item()
                st.session_state.facility_selected = ServiceFacility.get_facility__id(facility_id)
                st.session_state.facility_btn_form_edit = True
                
                UiComment.render_comments_block(st.session_state.facility_selected)
                UiTasks.render_tasks_block(st.session_state.facility_selected)
            else:
                st.session_state.facility_selected = None
                st.session_state.facility_btn_form_edit = False


    @staticmethod
    @st.dialog(title="Добавление Объекта",
               width="large",
               dismissible=False,
               on_dismiss="ignore")
    def render_dialog_add():
        """Диалоговое окно добавления Объекта"""
        if st.session_state.facility_show_form_add:
            license_names = ServiceLicense.get_license_names()
            license = st.selectbox("Лицензии", license_names)
            if license:
                facility_names = ServiceFacility.get_facility_names(license)
                parent = st.selectbox(label="Головной объект",
                                      options=facility_names)
            placeholder = st.empty()
            name = st.text_input(label='Наименование объекта')
            ftype_names = ServiceFacility.get_ftype_names()
            ftype = st.selectbox("Тип объекта", ftype_names)
            count = st.number_input(label='Количество')
            length = st.number_input(label='Протяженность')
            square = st.number_input(label='Площадь')
            note = st.text_area(label='Примечание')
            col1_btn, col2_btn, col3_btn = st.columns([1, 1, 7])
            with col1_btn:
                if st.button("Сохранить", width='stretch'):
                    if not name.strip():
                        placeholder.error("Поле 'Наименование объекта' обязательно для заполнения!")
                    elif not license.strip():
                        placeholder.error("Лицензия' обязательно для заполнения!")
                    elif not ftype.strip():
                        placeholder.error("Тип объекта' обязательно для заполнения!")
                    else:
                        res, msg = ServiceFacility.db_facility_insert(name, count, length, square, license, ftype, note, parent)
                        placeholder.success(msg) if res else placeholder.error(msg)
                    time.sleep(1)
                    UiFacility.dialog_add_btn_edit()
                    Helpers.form_close('facility_show_form_add')
            with col2_btn:
                if st.button("Отмена", width='stretch'):
                    UiFacility.dialog_add_btn_edit()
                    Helpers.form_close('facility_show_form_add')


    @staticmethod
    @st.dialog(title="Редактирование Объекта",
               width="large",
               dismissible=False,
               on_dismiss="ignore")
    def render_dialog_edit():
        """Диалоговое окно редактирования Объекта"""
        if st.session_state.facility_show_form_edit:
            # Предварительная полготовка данных
            facility = st.session_state.facility_selected
            if facility:
                placeholder = st.empty()
                license_names = ServiceLicense.get_license_names()
                lic = ServiceLicense.get_license__id(facility.license)
                index_license = license_names.index(lic.name)
                license = st.selectbox("Лицензии", license_names, index=index_license)
                index_parent = 0
                facility_names = ServiceFacility.get_facility_names(license)
                if license == lic.name:
                    if facility.parent:
                        facility_parent = ServiceFacility.get_facility__id(facility.parent)
                        index_parent = facility_names.index(facility_parent.name)
                        parent = st.selectbox("Головной объект", facility_names, index=index_parent)
                    else:
                        parent = st.selectbox("Головной объект", facility_names)
                else:
                    parent = st.selectbox("Головной объект", facility_names)
                        
                placeholder = st.empty()
                name = st.text_input('Наименование объекта', value=facility.name)
                ftype_names = ServiceFacility.get_ftype_names()
                ftype = ServiceFacility.get_ftype__id(facility.ftype)
                index_ftype = ftype_names.index(ftype.name)
                ftype = st.selectbox("Тип объекта", ftype_names, index=index_ftype)
                count = st.number_input(label='Количество', value=facility.count)
                length = st.number_input(label='Протяженность', value=facility.length)
                square = st.number_input(label='Площадь', value=facility.square)
                note = st.text_area("Примечание", value=facility.note)
                actual = st.checkbox("Актуальность", value=facility.actual)
    
                col1_btn, col2_btn, col3_btn = st.columns([1, 1, 7])
                with col1_btn:
                    if st.button("Сохранить", width='stretch'):
                        if not name.strip():
                            placeholder.error("Поле 'Наименование объекта' обязательно для заполнения!")
                        elif not license.strip():
                            placeholder.error("Лицензия' обязательно для заполнения!")
                        elif not ftype.strip():
                            placeholder.error("Тип объекта' обязательно для заполнения!")
                        else:
                            res, msg = ServiceFacility.db_facility_update(facility.id, name, count, length, square, license, ftype, note, actual, parent)
                            placeholder.success(msg) if res else placeholder.error(msg)
                        time.sleep(1)
                        UiFacility.dialog_add_btn_edit()
                        Helpers.form_close('facility_show_form_edit')
                with col2_btn:
                    if st.button("Отмена", width='stretch'):
                        UiFacility.dialog_add_btn_edit()
                        Helpers.form_close('facility_show_form_edit')
            else:
                UiFacility.dialog_add_btn_edit()
                Helpers.form_close('facility_show_form_edit')


    @staticmethod
    def dialog_add_btn_edit():
        """Костыль для того, что бы кнопка редактирования Объекта не жила собственной жизнью"""
        if st.session_state.facility_selected:
            st.session_state.facility_btn_form_edit = False
        else:
            st.session_state.facility_btn_form_edit = True

    @staticmethod
    @st.dialog(title="Добавление Типа Объекта",
               width="small",
               dismissible=False,
               on_dismiss="ignore")
    def render_dialog_add_ftype():
        """Диалоговое окно добавления Типа Объекта"""
        if st.session_state.ftype_show_form_add:
            placeholder = st.empty()
            name = st.text_input(label='Наименование типа объекта')
            col1_btn, col2_btn, col3_btn = st.columns([1, 1, 1])
            with col1_btn:
                if st.button("Сохранить", width='stretch'):
                    if not name.strip():
                        placeholder.error("Поле 'Наименование типа объекта' обязательно для заполнения!")
                    else:
                        res, msg = ServiceFacility.db_ftype_insert(name)
                        placeholder.success(msg) if res else placeholder.error(msg)
                    time.sleep(1)
                    Helpers.form_close('ftype_show_form_add')
            with col2_btn:
                if st.button("Отмена", width='stretch'):
                    Helpers.form_close('ftype_show_form_add')
        else:
            Helpers.form_close('ftype_show_form_add')