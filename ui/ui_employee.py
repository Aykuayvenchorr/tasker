import time
import pandas as pd
import datetime
import streamlit as st
from utils.helpers import Helpers
from services.service_employee import ServiceEmployee
from services.service_company import ServiceCompany
from services.service_division import ServiceDivision


class UiEmployee:
    """Класс работы со структурой Сотрудников"""

    @staticmethod
    def init_page():
        """Начальные настройки страницы Сотрудников"""
        # Проверка корректности попадания на страницу
        if 'employee_show_form_edit' not in st.session_state:
            st.warning("👿 Не корректное попадание на данную страницу")
            with st.spinner("🛸 Переход на главную страницу..."):
                time.sleep(1)
            st.switch_page('app.py')

        # Сброс стейтов
        st.session_state.employee_show_form_add = False
        st.session_state.employee_show_form_edit = False


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
                         key='employee_btn_add',
                         width='stretch',
                         icon=':material/add_task:'):
                st.session_state.employee_show_form_add = True
                UiEmployee.render_dialog_add()
            if st.button(label='Редактировать',
                         key='employee_btn_edit',
                         width='stretch',
                         icon=':material/edit_note:',
                         disabled=st.session_state.employee_btn_form_edit):
                st.session_state.employee_show_form_edit = True
                UiEmployee.render_dialog_edit()


    @staticmethod
    def render_header():
        """Шапка страницы"""
        st.title('🤸‍♂️ Сотрудники')
        st.divider()

    @staticmethod
    def render_table():
        switch_actual = st.checkbox(label='Только актуальные Сотрудники',
                            key='employee_checkbox',
                            value=True)
        is_df, df = ServiceEmployee.get_dataframe(switch_actual)
        if is_df:
            event_employee = st.dataframe(df,
                             on_select='rerun',
                             selection_mode='single-row',
                             width='content',
                             column_config={
                                 'ID': st.column_config.NumberColumn(
                                     label='ID',
                                     width='small',
                                     help='Id Сотрудника в БД'
                                 ),
                                 'name': st.column_config.TextColumn(
                                     label='Имя',
                                     width='content',
                                     help='Имяи'
                                 ),
                                 'surname': st.column_config.TextColumn(
                                     label='Фамилия',
                                     width='content',
                                     help='Фамилия'
                                 ),
                                 'patronymic': st.column_config.TextColumn(
                                     label='Отчество',
                                     width='content',
                                     help='Отчество'
                                 ),
                                 'company': st.column_config.TextColumn(
                                     label='Компания',
                                     width='content',
                                     help='Компания'
                                 ),
                                 'division': st.column_config.TextColumn(
                                     label='Подразделение',
                                     width='content',
                                     help='Подразделение'
                                 ),
                                 'post': st.column_config.TextColumn(
                                     label='Должность',
                                     width='content',
                                     help='Должность'
                                 ),
                                 'actual': st.column_config.CheckboxColumn(
                                     label='Актуальность',
                                     width='content',
                                     help='Актуальна ли информация'
                                 ),
                             })
            st.write('')

            # Обработка события выбора компании
            if event_employee.selection.rows:
                employee_id = df.loc[event_employee.selection.rows, 'ID'].item()
                st.session_state.employee_selected = ServiceEmployee.get_employee__id(employee_id)
                st.session_state.employ_btn_form_edit = True
                
            else:
                st.session_state.employee_selected = None
                st.session_state.employee_btn_form_edit = False


    @staticmethod
    @st.dialog(title="Добавление Сотрудника",
               width="large",
               dismissible=False,
               on_dismiss="ignore")
    def render_dialog_add():
        """Диалоговое окно добвления Сотрудника"""
        if st.session_state.employee_show_form_add:
            placeholder = st.empty()
            company_names = ServiceCompany.get_company_names()
            company = st.selectbox("Компании", company_names)
            division_names = ServiceDivision.get_division_names(company)
            division = st.selectbox("Подразделение", division_names)
            name = st.text_input('Имя')
            surname = st.text_input('Фамилия')
            patronymic = st.text_input('Отчество')
            post = st.text_input('Должность')
            isdirector = st.checkbox("Руководитель",
                                         value=False)
            isadmin = st.checkbox("Администратор",
                                      value=False)
            login = st.text_input('Логин')
            password = st.text_input('Пароль')
            phone = st.text_input("Телефон")
            email = st.text_input("Электронная почта")
            date_birth = st.date_input("Дата рождения",
                                           min_value=datetime.date(1900, 1, 1))
            contacts = st.text_area("Контакты")
            note = st.text_input(label='Примечание')

            col1_btn, col2_btn, col3_btn = st.columns([1, 1, 7])
            with col1_btn:
                if st.button("Сохранить", width='stretch'):
                    if not name.strip():
                        st.error("Поле 'Имя' обязательно для заполнения!")
                    if not surname.strip():
                        st.error("Поле 'Фамилия' обязательно для заполнения!")
                    if not post.strip():
                        st.error("Поле 'Должность' обязательно для заполнения!")
                    else:
                        res, msg = ServiceEmployee.db_employee_insert(name, surname, patronymic, post, isdirector, isadmin, login, password, phone, email, date_birth, contacts, company, division, note)
                        placeholder.success(msg) if res else placeholder.error(msg)
                    time.sleep(1)
                    UiEmployee.dialog_add_btn_edit()
                    Helpers.form_close('employee_show_form_add')
            with col2_btn:
                if st.button("Отмена", width='stretch'):
                    UiEmployee.dialog_add_btn_edit()
                    Helpers.form_close('employee_show_form_add')


    @staticmethod
    @st.dialog(title="Редактирование Сотрудника",
               width="large",
               dismissible=False,
               on_dismiss="ignore")
    def render_dialog_edit():
        """Диалоговое окно редактирования Сотрудника"""
        if st.session_state.employee_show_form_edit:
            # Предварительная полготовка данных
            emp = st.session_state.employee_selected
            placeholder = st.empty()
            cmp = ServiceCompany.get_company__id(emp.company)
            div = ServiceDivision.get_division__id(emp.division)
            
            company_names = ServiceCompany.get_company_names()
            index_company = company_names.index(cmp.name)
            
            company = st.selectbox("Компании", company_names, index=index_company)
            if company == cmp.name:
                division_names = ServiceDivision.get_division_names(company)
                index_division = division_names.index(div.name)
                division = st.selectbox("Подразделения", division_names, index=index_division)
            else:
                division_names = ServiceDivision.get_division_names(company)
                division = st.selectbox("Подразделения", division_names)
            
            name = st.text_input('Имя', value=emp.name)
            surname = st.text_input('Фамилия', value=emp.surname)
            patronymic = st.text_input('Отчество', value=emp.patronymic)
            post = st.text_input('Должность', value=emp.post)
            isdirector = st.checkbox("Руководитель", value=emp.isdirector)
            isadmin = st.checkbox("Администратор", value=emp.isadmin)
            login = st.text_input('Логин', value=emp.login)
            password = st.text_input('Пароль', value=emp.password)
            phone = st.text_input("Телефон", value=emp.phone)
            email = st.text_input("Электронная почта", value=emp.email)
            date_birth = st.date_input("Дата рождения",
                                       value=emp.date_birth,
                                       min_value=datetime.date(1900, 1, 1))
            contacts = st.text_area("Контакты", value=emp.contacts)
            note = st.text_area("Примечание", value=emp.note)
            actual = st.checkbox("Актуальность", value=emp.actual)

            col1_btn, col2_btn, col3_btn = st.columns([1, 1, 7])
            with col1_btn:
                if st.button("Сохранить", width='stretch'):
                    if not name.strip():
                        st.error("Поле 'Имя' обязательно для заполнения!")
                    if not surname.strip():
                        st.error("Поле 'Фамилия' обязательно для заполнения!")
                    if not post.strip():
                        st.error("Поле 'Должность' обязательно для заполнения!")
                    if not company.strip():
                        st.error("Поле 'Компания' обязательно для выбора!")
                    if not division.strip():
                        st.error("Поле 'Подразделение' обязательно для выбора!")
                    if not login.strip():
                        st.error("Поле 'Логин' обязательно для заполнения!")
                    if not password.strip():
                        st.error("Поле 'Пароль' обязательно для заполнения!")
                    else:
                        res, msg = ServiceEmployee.db_employee_update(emp.id, name, surname, patronymic, post, isdirector, isadmin, login, password, phone, email, date_birth, contacts, company, division, note, actual)
                        placeholder.success(msg) if res else placeholder.error(msg)
                    time.sleep(1)
                    UiEmployee.dialog_add_btn_edit()
                    Helpers.form_close('employee_show_form_edit')
            with col2_btn:
                if st.button("Отмена", width='stretch'):
                    UiEmployee.dialog_add_btn_edit()
                    Helpers.form_close('employee_show_form_edit')
        else:
            UiEmployee.dialog_add_btn_edit()
            Helpers.form_close('employee_show_form_edit')


    @staticmethod
    def dialog_add_btn_edit():
        """Костыль для того, что бы кнопка редактирования Сотрудника не жила собственной жизнью"""
        if st.session_state.employee_selected:
            st.session_state.employee_btn_form_edit = False
        else:
            st.session_state.employee_btn_form_edit = True