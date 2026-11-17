import time
import streamlit as st
from utils.helpers import Helpers
from ui.ui_auth import UiAuth
from services.service_task import ServiceTask
from services.service_company import ServiceCompany
from services.service_license import ServiceLicense
from services.service_division import ServiceDivision
from services.service_facility import ServiceFacility
from services.service_project import ServiceProject
from services.service_auth import ServiceAuth


class UiTasks:
    """Пользовательский интерфейс работы с задачами"""

    @staticmethod
    def render_struct():
        """Выпадающий список структуры"""
        with st.expander('Структура', expanded=False, icon='🏛'):
            st.page_link('pages/pg_company.py', label='Компании', icon=':material/source_environment:')
            st.page_link('pages/pg_division.py', label='Подразделения', icon=':material/diversity_3:')
            st.page_link('pages/pg_license.py', label='Лицензии', icon=':material/news:')
            st.page_link('pages/pg_project.py', label='Проекты', icon=':material/flowsheet:')
            st.page_link('pages/pg_facility.py', label='Объекты', icon=':material/oil_barrel:')
            st.page_link('pages/pg_employee.py', label='Сотрудники', icon=':material/conditions:')
            st.page_link('pages/pg_busplan.py', label='Бизнес-планы', icon=':material/cases:')
            # st.page_link('pages/businessplan.py', label='Бизнес-планы', icon=':material/cases:')
            # st.page_link('pages/monitoring.py', label='Мониторинги', icon=':material/monitoring:')

    @staticmethod
    def render_tasks_sidebar():
        """Боковая панель"""
        with st.sidebar:
            st.title(f'👋 Привет, {st.session_state.employee.name}!')
            st.divider()

            if ServiceTask.allowed_empoyee(st.session_state.employee):
                UiTasks.render_struct()


    @staticmethod
    def render_tasks():
        UiAuth.render_title_main()


    @staticmethod
    def render_tasks_block(obj) -> None:
        """Отображение блока задач"""
        st.divider()
        with st.expander(label='Задачи', icon=':material/pending_actions:'):
            switch_actual = st.checkbox(label='Только актуальные задачи', key='tasks_actual', value=True)
            task_col1_btn, task_col2_btn, task_col3_btn = st.columns([1, 1, 7])
            if task_col1_btn.button('Добавить', width='stretch', key='task_btn_add', icon=':material/edit_document:'):
                relation = ServiceTask.get_relation_from_object(obj)
                st.session_state.task_show_form_add = True
                UiTasks.render_dialog_task_add(relation=relation, parent=None)
            tasks = ServiceTask.get_tasks(obj, switch_actual)
            if tasks:
                for task in tasks:
                    UiTasks.render_task(task, switch_actual, None)

    @staticmethod
    def render_tasks_block_main_page(filt) -> None:
        """Отображение блока задач на главное странице"""
        switch_actual = st.checkbox(label='Только актуальные задачи', key='tasks_actual', value=True)
        task_col1_btn, task_col2_btn, task_col3_btn = st.columns([1, 1, 7])
        if task_col1_btn.button('Добавить', width='stretch', key='task_btn_add', icon=':material/edit_document:'):
            st.session_state.task_show_form_add = True
            UiTasks.render_dialog_task_add(relation=None, parent=None)
        tasks = ServiceTask.get_tasks_main_page(filt, switch_actual, st.session_state.employee.id)
        if tasks:
            for task in tasks:
                UiTasks.render_task(task, switch_actual, filt)

    @staticmethod
    def render_task(task, switch_actual, filt, field=None) -> None:
        """Отображение одной задачи"""
        color_label = '#c0c0c0'
        employee = ServiceAuth.get_employee__id(task.employee_responsible)
        plan_date_end = ServiceTask.get_plan_date_end(task.id)
        count_undone, count_all = ServiceTask.task_cont_children(task)
        importance, color = ServiceTask.get_task__importance(task.importance.name)
        dt_start, dt_end, p_f_dt, p_f_ct, p_d_dt, p_d_ct, p_nds, p_ndfl = ServiceTask.get_task_plane__start_end_costs(task.id)
        admin = ServiceAuth.get_admin(st.session_state.user)
        if 'expanded_tasks' in st.session_state:
            # print('st.session_state.expanded_tasks', st.session_state.expanded_tasks)
            if task.id in st.session_state.expanded_tasks:
                expanded = True
            else:
                expanded = False
        else:
            # print('нет тут ничего')
            expanded = False
        if task.actual:
            if admin:
                label = f'{importance}{count_all}/{count_undone} 🙋‍♂️*{employee.surname} {employee.name[0]}.{employee.patronymic[0]}.*: ({task.id}) **{task.name}**'
            else:
                label = f'{importance}{count_all}/{count_undone} 🙋‍♂️*{employee.surname} {employee.name[0]}.{employee.patronymic[0]}.*: **{task.name}**'
            icon = ':material/pending_actions:'
        else:
            if admin:
                label = f'{importance}{count_all}/{count_undone} 🙋‍♂️*{employee.surname} {employee.name[0]}.{employee.patronymic[0]}.*: ({task.id}) **~~{task.name}~~**'
            else:
                label = f'{importance}{count_all}/{count_undone} 🙋‍♂️*{employee.surname} {employee.name[0]}.{employee.patronymic[0]}.*: **~~{task.name}~~**'
            icon = ':material/assignment_turned_in:'
        with st.expander(label=label, icon=icon, expanded=expanded):
            r1c1, r1c2 = st.columns([1, 4])
            r1c1.badge(label=f'⏳{dt_start} / 🔥{dt_end}', color=color)
            if task.doc:
                if len(task.doc) >0:
                    r1c2.markdown(body=f'<font color="{color_label}">*Документы:</font>* {task.doc}', unsafe_allow_html=True)
            with st.container(border=True):
                st.text(task.desc)
            with st.expander(label='Примечания', icon=':material/speaker_notes:'):
                st.text(body=task.note if task.note != None else 'Пока здесь ничего нет')
            with st.expander(label='💸 Финансы', icon=':material/currency_ruble:'):
                pfin = f' <font color="{color_label}">📅 <ins>*Финансирование:*</ins></font> {p_f_dt} / {p_f_ct}₽' if p_f_dt != None else ''
                pdev = f' <font color="{color_label}">📅 <ins>*Освоение:*</ins></font> {p_d_dt} / {p_d_ct}₽' if p_d_dt != None else ''
                pnds = f' <font color="{color_label}"><ins>*НДС:*</ins></font> {p_nds}%' if p_nds != None else ''
                pndf = f' <font color="{color_label}"><ins>*НДФЛ:*</ins></font> {p_ndfl}%' if p_ndfl != None else ''
                st.markdown(body=f'💸 Планируемые:{pfin}{pdev}{pnds}{pndf}', unsafe_allow_html=True)
                ffin = f' <font color="{color_label}">📅 <ins>*Финансирование:*</ins></font> {task.fact_fin_dt} / {task.fact_fin_cost}₽' if task.fact_fin_dt != None else ''
                fdev = f' <font color="{color_label}">📅 <ins>*Освоение:*</ins></font> {task.fact_dev_dt} / {task.fact_dev_cost}₽' if task.fact_dev_dt != None else ''
                finf = f' <font color="{color_label}">👀 <ins>*Информация:*</ins></font> {task.cost_info}%' if task.cost_info != None else ''
                st.markdown(body=f'💸 Фактические:{ffin}{fdev}{finf}', unsafe_allow_html=True)
            btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 7])
            if btn_col1.button('Редактировать', key=f'btn_edittask_{task.id}', width='stretch', icon=':material/edit_document:'):
                st.session_state.task_show_form_edit = True
                UiTasks.render_dialog_task_edit(task)
            if btn_col2.button('Добавить подзадачу', key=f'btn_subtask_{task.id}', width='stretch', icon=':material/pending_actions:'):
                st.session_state.task_show_form_add = True
                relation = ServiceTask.get_task_hub(task)
                UiTasks.render_dialog_task_add(relation, task.id)
            if filt:
                children = ServiceTask.get_task_children(task, switch_actual, filt)
            else:
                children = ServiceTask.get_task_children_count(task, switch_actual)
                
            if len(children) > 0:
                for child in children:
                    UiTasks.render_task(child, switch_actual, filt)

    @staticmethod
    @st.dialog(title="Добавление задачи",
               width="large",
               dismissible=False,
               on_dismiss="ignore",
               icon=':material/pending_actions:')
    def render_dialog_task_add(relation, parent: int|None = None) -> None:
        """Диалоговое окно добавления Задачи"""
        if st.session_state.task_show_form_add:
            placeholder = st.empty()
            name = st.text_input(label='Задача *')
            desc = st.text_area('Описание задачи *')
            cnt_col1, cnt_col2, cnt_col3, cnt_col4 = st.columns([2, 1, 1, 1])
            employee_names_list = ServiceTask.get_employee_names()
            employee_responsible = cnt_col1.selectbox(label='💪 Ответственный *', options=employee_names_list, index=0)
            plandatestart = cnt_col2.date_input(label='⏳ Начало *', min_value='2000-01-01', max_value='2100-12-31', help='Планируемая дата начала задачи', format='YYYY-MM-DD')
            plandateend = cnt_col3.date_input(label='🔥 Завершение *', min_value='2000-01-01', max_value='2100-12-31', help='Планируемая дата завершения задачи', format='YYYY-MM-DD')
            importance = cnt_col4.selectbox(label='🚦 Важность задачи *', options=['⚫ Низкая', '🔵 Средняя', '🔴 Высокая'], index=1)
            doc = st.text_input(label='📂 Документы', help='Место размещения документов')
            with st.expander(label='💸 Планируемые финансы', icon=':material/currency_ruble:'):
                tf_col1, tf_col2, tf_col3, tf_col4, tf_col5, tf_col6 = st.columns([2, 2, 2, 2, 1, 1])
                plandatefin = tf_col1.date_input(label='📅 Финансирование', min_value='2000-01-01', max_value='2100-12-31', help='Планируемая дата финансирования', format='YYYY-MM-DD')
                plancostfin = tf_col2.number_input(label='Финансирование, руб.', value=0.00,  format='%0.2f', step=0.01, icon=':material/currency_ruble:')
                plandatedev = tf_col3.date_input(label='📅 Освоение', min_value='2000-01-01', max_value='2100-12-31', help='Планируемая дата освоения', format='YYYY-MM-DD')
                plancostdev = tf_col4.number_input(label='Освоение, руб.', value=0.00, format='%0.2f', icon=':material/currency_ruble:')
                plannds = tf_col5.number_input(label='НДС, %', value=0, icon=':material/percent:')
                planndfl = tf_col6.number_input(label='НДФЛ, %', value=0, icon=':material/percent:')
            with st.expander(label='🔖 Области задачи', icon=':material/hub:'):
                if relation:
                    companies, licenses, divisions, facilities, projects = UiTasks.render_task_hub_h(relation)
                else:
                    companies, licenses, divisions, facilities, projects = UiTasks.render_task_hub_h()
            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 7])
            if btn_col1.button('Сохранить', width='stretch'):
                result, msg = ServiceTask.db_task_insert(st.session_state.employee.id, name, desc, employee_responsible, importance, plandatestart, plandateend, doc, plandatefin, plancostfin, plandatedev, plancostdev, plannds, planndfl, parent, companies, divisions, licenses, projects, facilities)
                if result:
                    placeholder.success(msg, icon='👍')
                    time.sleep(1)
                    Helpers.form_close('task_show_form_add')
                else:
                    placeholder.error(msg, icon='👿')
                    time.sleep(1)
                    Helpers.form_close('task_show_form_add')
            if btn_col2.button('Отменить', width='stretch'):
                Helpers.form_close('task_show_form_add')

    @staticmethod
    def render_task_hub_h(relation=None, db_companies=None, db_licenses=None, db_facilities=None, db_divisions=None, db_projects=None):
        """Рисовка отношений задачи"""
        if relation:
            companies_selected, companies_list = ServiceCompany.get_companies(relation['companies'])
        else:
            companies_selected, companies_list = ServiceCompany.get_companies([])
        db_companies = st.multiselect(label='Компании', options=companies_list, format_func=Helpers.format_label, default=companies_selected)
        tr_col1, tr_col2 = st.columns([1, 1])
        if len(db_companies) > 0:
            if relation:
                licenses_selected, licenses_list = ServiceLicense.get_licenses__companies(db_companies, relation['licenses'])
                divisions_selected, divisions_list = ServiceDivision.get_divisions__companies(db_companies, relation['divisions'])
            else:
                licenses_selected, licenses_list = ServiceLicense.get_licenses__companies(db_companies, [])
                divisions_selected, divisions_list = ServiceDivision.get_divisions__companies(db_companies, [])
                
            db_licenses = tr_col1.multiselect(label='Лицензии', options=licenses_list, default=licenses_selected)
            db_divisions = tr_col2.multiselect(label='Подразделения', options=divisions_list, format_func=Helpers.format_label_list, default=divisions_selected)
            if len(db_licenses) > 0:
                if relation:
                    facilities_selected, facilities_list = ServiceFacility.get_facilities__licenses(db_licenses, relation['facilities'])
                else:
                    facilities_selected, facilities_list = ServiceFacility.get_facilities__licenses(db_licenses, [])
                    
                db_facilities = tr_col1.multiselect(label='Объекты', options=facilities_list, format_func=Helpers.format_label_list, default=facilities_selected)
            if len(db_divisions) > 0 or len(db_licenses) > 0:
                if relation:
                    projects_selected, projects_list = ServiceProject.get_projects__licenses_divisions(db_licenses, db_divisions, relation['projects'])
                else:
                    projects_selected, projects_list = ServiceProject.get_projects__licenses_divisions(db_licenses, db_divisions, [])
                    
                db_projects = tr_col2.multiselect(label='Проекты', options=projects_list, default=projects_selected)
        return db_companies, db_licenses, db_divisions, db_facilities, db_projects


    @staticmethod
    @st.dialog(title="Редактирование задачи",
               width="large",
               dismissible=False,
               on_dismiss="ignore",
               icon=':material/edit_document:')
    def render_dialog_task_edit(task) -> None:
        """Диалоговое окно редактирования Задачи"""
        if st.session_state.task_show_form_edit:
            placeholder = st.empty()
            # st.session_state.expanded_tasks = []
            admin = ServiceAuth.get_admin(st.session_state.user)
            if admin:
                task_parent = st.text_input(label='Головная задача', value=task.parent)
            else:
                task_parent = task.parent
            name = st.text_input(label='Задача *', value=task.name)
            desc = st.text_area('Описание задачи *', value=task.desc)
            cnt_col1, cnt_col2, cnt_col3, cnt_col4, cnt_col5 = st.columns([2, 1, 1, 1, 1])
            employee_names_list = ServiceTask.get_employee_names()
            employee_names_list.pop(0)
            index = ServiceTask.get_employee_names_index(employee_names_list, task.employee_responsible)
            employee_responsible = cnt_col1.selectbox(label='💪 Ответственный *', options=employee_names_list, index=index)
            dt_start, dt_end, p_f_dt, p_f_ct, p_d_dt, p_d_ct, p_nds, p_ndfl = ServiceTask.get_task_plane__start_end_costs(task.id)
            plandatestart = cnt_col2.date_input(label='⏳ Начало *', min_value='2000-01-01', max_value='2100-12-31', help='Планируемая дата начала задачи', format='YYYY-MM-DD', value=dt_start)
            plandateend = cnt_col3.date_input(label='🔥 Завершение *', min_value='2000-01-01', max_value='2100-12-31', help='Планируемая дата завершения задачи', format='YYYY-MM-DD', value=dt_end)
            index_importance, index_status = ServiceTask.get_index__importance_status(task.importance.value, task.status.value)
            importance = cnt_col4.selectbox(label='🚦 Важность задачи *', options=['⚫ Низкая', '🔵 Средняя', '🔴 Высокая'], index=index_importance)
            count_undone, count_all = ServiceTask.task_cont_children(task)

            if count_undone > 0:
                status = cnt_col5.selectbox(label='⏰ Статус задачи *', options=['🧘‍♂️ Не начата', '👨‍🔧 В работе'], index=index_status)
            else:
                status = cnt_col5.selectbox(label='⏰ Статус задачи *', options=['🧘‍♂️ Не начата', '👨‍🔧 В работе', '🙅‍♂️ Отменена', '💃 Завершена'], index=index_status)
            doc = st.text_input(label='📂 Документы', help='Место размещения документов', value=task.doc)
            with st.expander(label='💸 Планируемые финансы', icon=':material/currency_ruble:'):
                tp_col1, tp_col2, tp_col3, tp_col4, tp_col5, tp_col6 = st.columns([2, 2, 2, 2, 1, 1])
                plandatefin = tp_col1.date_input(label='📅 Финансирование', min_value='2000-01-01', max_value='2100-12-31', help='Планируемая дата финансирования', format='YYYY-MM-DD', value=p_f_dt)
                plancostfin = tp_col2.number_input(label='Финансирование, руб.', format='%0.2f', step=0.01, icon=':material/currency_ruble:', value=p_f_ct)
                plandatedev = tp_col3.date_input(label='📅 Освоение', min_value='2000-01-01', max_value='2100-12-31', help='Планируемая дата освоения', format='YYYY-MM-DD', value=p_d_dt)
                plancostdev = tp_col4.number_input(label='Освоение, руб.', format='%0.2f', icon=':material/currency_ruble:', value=p_d_ct)
                plannds = tp_col5.number_input(label='НДС, %', icon=':material/percent:', value=p_nds)
                planndfl = tp_col6.number_input(label='НДФЛ, %', icon=':material/percent:', value=p_ndfl)
            with st.expander(label='💸 Фактические финансы', icon=':material/currency_ruble:'):
                tf_col1, tf_col2, tf_col3, tf_col4, tf_col5 = st.columns([2, 2, 2, 2, 2])
                factdatefin = tf_col1.date_input(label='📅 Финансирование', min_value='2000-01-01', max_value='2100-12-31', help='Планируемая дата финансирования', format='YYYY-MM-DD', value=task.fact_fin_dt, key='factdatefin')
                factcostfin = tf_col2.number_input(label='Финансирование, руб.', format='%0.2f', step=0.01, icon=':material/currency_ruble:', value=task.fact_fin_cost, key='factcostfin')
                factdatedev = tf_col3.date_input(label='📅 Освоение', min_value='2000-01-01', max_value='2100-12-31', help='Планируемая дата освоения', format='YYYY-MM-DD', value=task.fact_dev_dt, key='factdatedev')
                factcostdev = tf_col4.number_input(label='Освоение, руб.', format='%0.2f', icon=':material/currency_ruble:', value=task.fact_dev_cost, key='factcostdev')
                factinfo = tf_col5.text_input(label='👀 Информация', value=task.cost_info)
            with st.expander(label='🔖 Области задачи', icon=':material/hub:'):
                relation = ServiceTask.get_task_hub(task)
                companies, licenses, divisions, facilities, projects = UiTasks.render_task_hub_h(relation)
            note = st.text_area('📌 Примечания', value=task.note)
            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 7])
            if btn_col1.button('Сохранить', width='stretch'):
                st.session_state.expanded_tasks = []
                st.session_state.expanded_tasks = ServiceTask.expanded_tasks(task.id)
                result, msg = ServiceTask.db_task_update(st.session_state.employee.id, task.id, task_parent, name, desc, employee_responsible, importance, status, plandatestart, plandateend, doc, plandatefin, plancostfin, plandatedev, plancostdev, plannds, planndfl, factdatefin, factcostfin, factdatedev, factcostdev, factinfo, note, companies, divisions, licenses, projects, facilities)
                if result:
                    placeholder.success(msg, icon='👍')
                    Helpers.form_close('task_show_form_edit')
                else:
                    placeholder.error(msg, icon='👿')
                    Helpers.form_close('task_show_form_edit')
            if btn_col2.button('Отменить', width='stretch'):
                    Helpers.form_close('task_show_form_edit')