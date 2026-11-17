import time
import streamlit as st
import pandas as pd

from datetime import date

from utils.helpers import Helpers

from services.service_busplanstr import ServiceBusplanStr
from services.service_busplan import ServiceBusplan
from services.service_project import ServiceProject
from services.service_task import ServiceTask
from models import TaskImportanceEnum
from ui.ui_tasks import UiTasks


class UiBusplanStr:
    """Интерфейс строк бизнес-плана, сроков, оплат и связанных задач."""

    # =========================================================
    # 1. ТАБЛИЦА СТРОК БИЗНЕС-ПЛАНА
    # =========================================================
    @staticmethod
    def render_table(busplan_id):
    
        rows = ServiceBusplanStr.get_busplanstr_by_busplan(busplan_id)
    
        if not rows:
            st.info("Строки бизнес-плана пока не добавлены.")
            return
    
        df = pd.DataFrame(rows)
    
        # Сохраняем полный DataFrame для определения выбранной строки
        df_display = df.drop(columns=["bpstr_id", "company_id", "job_id"])
    
        event = st.dataframe(
            df_display,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            width="stretch"
        )
    
        selected_rows = event.selection.rows
    
        if selected_rows:
            selected_index = selected_rows[0]
    
            # Получаем ID строки БП, даже если выбрана вторая или третья оплата
            bpstr_id = df.iloc[selected_index]["bpstr_id"]
            job_id = df.iloc[selected_index]["job_id"]
    
            st.session_state["bpstr_selected_id"] = bpstr_id
            st.session_state["job_selected_id"] = job_id
    
        bpstr_id = st.session_state.get("bpstr_selected_id")
        job_id = st.session_state.get("job_selected_id")
        
        if bpstr_id:
            st.button(
                "Добавить сроки, оплату и задачу",
                type="primary",
                key="add_job_task",
                on_click=lambda: st.session_state.update({
                    "show_add_job_task": True
                })
            )
    
        if st.session_state.get("show_add_job_task") and bpstr_id:
            UiBusplanStr.render_dialog_add_job_task(bpstr_id)

        st.divider()
        st.subheader("Задачи по выбранной строке")
        if job_id is None:
            st.info("Выбери строку с оплатой, чтобы увидеть связанные задачи.")
        
        else:
            switch_actual = st.checkbox(
                "Только актуальные задачи",
                value=True,
                key=f"job_tasks_actual_{job_id}"
            )
        
            tasks = ServiceTask.get_tasks_by_job(job_id)
        
            if tasks:
                for task in tasks:
                    UiTasks.render_task(
                        task=task,
                        switch_actual=switch_actual,
                        filt=None
                    )
            else:
                st.info("К выбранной оплате задачи ещё не привязаны.")



    # =========================================================
    # 2. ДОБАВЛЕНИЕ СТРОКИ БИЗНЕС-ПЛАНА
    # =========================================================

    @staticmethod
    @st.dialog(
        title="Добавление строки бизнес-плана",
        width="large",
        dismissible=False,
        on_dismiss="ignore"
    )
    def render_dialog_add():

        busplan = st.session_state.get("busplan_selected")

        if not busplan:
            st.warning("Сначала выберите бизнес-план.")
            return

        placeholder = st.empty()

        st.subheader(f"Бизнес-план: {busplan.name}")

        options = ServiceBusplanStr.get_form_options(busplan.project)

        if options is None:
            st.error("Не удалось загрузить данные для заполнения формы.")
            return

        st.subheader("Строка бизнес-плана")

        # Значение по умолчанию — ГПН-ГЕО.
        company_index = next(
            (
                i for i, company in enumerate(options["companies"])
                if company[1] == "ГПН-ГЕО"
            ),
            0
        )

        # Значение по умолчанию — Поиск.
        stage_index = next(
            (
                i for i, stage in enumerate(options["stages"])
                if stage[1] == "Поиск"
            ),
            0
        )

        company_id = UiBusplanStr.select_option(
            "Компания",
            options["companies"],
            "bpstr_company",
            index=company_index
        )

        facility_id = UiBusplanStr.select_option(
            "Объект бизнес-плана",
            options["facilities"],
            "bpstr_facility"
        )

        costitem_id = UiBusplanStr.select_option(
            "Статья затрат",
            options["costitems"],
            "bpstr_costitem"
        )

        stage_id = UiBusplanStr.select_option(
            "Этап проекта",
            options["stages"],
            "bpstr_stage",
            index=stage_index
        )

        st.divider()

        col1, col2 = st.columns([1, 1])

        with col1:
            save = st.button(
                "Сохранить",
                width="stretch",
                type="primary"
            )

        with col2:
            cancel = st.button(
                "Отмена",
                width="stretch"
            )

        if cancel:
            Helpers.form_close("busplanstr_show_form_add")

        if save:

            if company_id is None:
                placeholder.error("Необходимо выбрать компанию.")
                return

            try:
                res, msg = ServiceBusplanStr.db_busplanstr_insert(
                    businessplan_id=busplan.id,
                    company_id=company_id,
                    facility_id=facility_id,
                    costitem_id=costitem_id,
                    stage_id=stage_id
                )

                if res:
                    placeholder.success(msg)
                    time.sleep(1)

                    st.session_state.pop("bpstr_selected", None)

                    Helpers.form_close("busplanstr_show_form_add")

                else:
                    placeholder.error(msg)

            except Exception as e:
                placeholder.error(
                    f"Ошибка при создании строки бизнес-плана: {e}"
                )

    # =========================================================
    # 3. ДОБАВЛЕНИЕ JOB И TASK К ВЫБРАННОЙ СТРОКЕ БП
    # =========================================================

    @staticmethod
    @st.dialog(
        title="Добавление сроков, оплаты и задачи",
        width="large",
        dismissible=False,
        on_dismiss="ignore"
    )
    def render_dialog_add_job_task(bpstr_id):

        busplan_selected = st.session_state.get("busplan_selected")

        if not busplan_selected:
            st.warning("Не выбран бизнес-план.")
            return

        st.subheader(
            f"Строка бизнес-плана № {bpstr_id}"
        )

        options = ServiceBusplanStr.get_form_options(
            busplan_selected.project
        )

        if options is None:
            st.error("Не удалось загрузить данные для заполнения формы.")
            return

        # -----------------------------------------------------
        # 1. СРОКИ И ОПЛАТА (JOB)
        # -----------------------------------------------------

        st.subheader("Сроки и оплата")

        col1, col2 = st.columns(2)

        with col1:

            dt_start = st.date_input(
                "⏳ Начало",
                value=date.today(),
                key=f"job_dt_start_{bpstr_id}"
            )

            plan_dev_dt = st.date_input(
                "📅 Дата освоения",
                value=date.today(),
                key=f"job_plan_dev_dt_{bpstr_id}"
            )

            plan_dev_cost = st.number_input(
                "Освоение, руб.",
                min_value=0.0,
                value=0.0,
                key=f"job_plan_dev_cost_{bpstr_id}"
            )

        with col2:

            dt_end = st.date_input(
                "🔥 Завершение",
                value=date.today(),
                key=f"job_dt_end_{bpstr_id}"
            )

            plan_fin_dt = st.date_input(
                "📅 Дата финансирования",
                value=date.today(),
                key=f"job_plan_fin_dt_{bpstr_id}"
            )

            plan_fin_cost = st.number_input(
                "Финансирование, руб.",
                min_value=0.0,
                value=0.0,
                key=f"job_plan_fin_cost_{bpstr_id}"
            )

        st.divider()

        # -----------------------------------------------------
        # 2. ДАННЫЕ ЗАДАЧИ
        # -----------------------------------------------------

        st.subheader("Задача")

        task_name = st.text_input(
            "Наименование задачи",
            key=f"job_task_name_{bpstr_id}"
        )

        task_desc = st.text_area(
            "Описание задачи",
            key=f"job_task_desc_{bpstr_id}"
        )

        employee_responsible = UiBusplanStr.select_option(
            "Ответственный",
            options["employees"],
            f"job_employee_{bpstr_id}"
        )

        importance_names = {
            TaskImportanceEnum.LOW: "Низкая",
            TaskImportanceEnum.MIDDLE: "Средняя",
            TaskImportanceEnum.HIGH: "Высокая"
        }

        importance = st.selectbox(
            "Важность задачи",
            options=list(importance_names.keys()),
            format_func=lambda x: importance_names[x],
            key=f"job_task_importance_{bpstr_id}",
            index=2
        )

        doc = st.text_input(
            "📂 Документы",
            help="Место размещения документов",
            key=f"job_task_doc_{bpstr_id}"
        )

        # -----------------------------------------------------
        # 3. ОБЛАСТИ ЗАДАЧИ
        # -----------------------------------------------------

        busplan = ServiceBusplan.get_busplan__id(
            busplan_selected.id
        )

        project = ServiceProject.get_project_by_busplan_id(
            busplan.id
        )

        company_ids = ServiceProject.get_project_license_companies(
            project.id
        )

        license_ids = ServiceProject.get_project_licenses(
            project.id
        )

        # Компания строки БП должна входить в области задачи.
        bpstr_rows = ServiceBusplanStr.get_busplanstr_by_busplan(
            busplan.id
        )

        selected_row = next(
            (
                row for row in bpstr_rows
                if row["bpstr_id"] == bpstr_id
            ),
            None
        )

        if selected_row:
            selected_company_id = selected_row.get("company_id")

            if selected_company_id and selected_company_id not in company_ids:
                company_ids.append(selected_company_id)

        relation = {
            "companies": company_ids,
            "divisions": [project.division],
            "projects": [busplan.project],
            "licenses": license_ids,
            "facilities": []
        }

        with st.expander(
            label="🔖 Области задачи",
            icon=":material/hub:"
        ):

            companies, licenses, divisions, facilities, projects = (
                UiTasks.render_task_hub_h(relation)
            )

        st.divider()

        # -----------------------------------------------------
        # 4. СОХРАНЕНИЕ
        # -----------------------------------------------------

        col1_btn, col2_btn = st.columns([1, 1])

        with col1_btn:

            save = st.button(
                "Сохранить",
                type="primary",
                width="stretch",
                key=f"save_job_task_{bpstr_id}"
            )

        with col2_btn:

            cancel = st.button(
                "Отмена",
                width="stretch",
                key=f"cancel_job_task_{bpstr_id}"
            )

        if cancel:
            st.session_state["show_add_job_task"] = False
            st.rerun()

        if save:

            if not task_name.strip():
                st.error(
                    "Поле «Наименование задачи» обязательно для заполнения!"
                )
                return

            employee_created = st.session_state.employee.id

            try:

                res, msg = ServiceBusplanStr.db_job_task_insert(
                    bpstr_id=bpstr_id,

                    # Данные Job
                    dt_start=dt_start,
                    dt_end=dt_end,
                    plan_fin_dt=plan_fin_dt,
                    plan_fin_cost=plan_fin_cost,
                    plan_dev_dt=plan_dev_dt,
                    plan_dev_cost=plan_dev_cost,

                    # Данные Task
                    task_name=task_name.strip(),
                    task_desc=task_desc or None,
                    employee_created=employee_created,
                    employee_responsible=employee_responsible,
                    importance=importance,
                    doc=doc or None,

                    # Области задачи
                    companies=companies,
                    licenses=licenses,
                    divisions=divisions,
                    facilities=facilities,
                    projects=projects
                )

                if res:
                    st.success(msg)
                    time.sleep(1)
                    st.session_state["show_add_job_task"] = False
                    st.rerun()

                else:
                    st.error(msg)

            except Exception as e:
                st.error(
                    f"Ошибка при создании сроков, оплаты и задачи: {e}"
                )

    # =========================================================
    # 4. ВЫПАДАЮЩИЙ СПИСОК
    # =========================================================

    @staticmethod
    def select_option(label, options, key, index=0):
        """
        Выпадающий список с возможностью не выбирать значение.

        options: список кортежей (id, name).
        Возвращает ID выбранного элемента.
        """

        if not options:
            st.warning(f"Нет доступных значений для поля «{label}».")
            return None

        selected = st.selectbox(
            label,
            options=options,
            format_func=lambda x: x[1],
            key=key,
            index=index
        )

        return selected[0]
