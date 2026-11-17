from models import (
    SessionLocal,
    BusinessPlanStr,
    Job,
    Task,
    Company,
    Division,
    Facility,
    BusinessPlanFacility,
    BusinessPlanCostItem,
    ProjectStage,
    Employee,
    TaskStatusEnum,
    PlanDateStart,
    PlanDateEnd,
    PlanCost
)


class ServiceBusplanStr:
    """Сервис работы со строками бизнес-плана, сроками, оплатами и задачами."""

    # =========================================================
    # 1. ПОЛУЧЕНИЕ СТРОК БИЗНЕС-ПЛАНА
    # =========================================================

    @staticmethod
    def get_busplanstr_by_busplan(busplan_id):
        """Получить строки бизнес-плана вместе со всеми сроками и оплатами."""
    
        with SessionLocal() as db:
    
            rows = (
                db.query(
                    BusinessPlanStr.id.label("bpstr_id"),
                    BusinessPlanStr.company.label("company_id"),
    
                    Company.name.label("company_name"),
                    ProjectStage.name.label("stage_name"),
                    BusinessPlanFacility.name.label("facility_name"),
                    BusinessPlanCostItem.name.label("costitem_name"),
    
                    Job.id.label("job_id"),
                    Job.dt_start.label("dt_start"),
                    Job.dt_end.label("dt_end"),
                    Job.plan_fin_dt.label("plan_fin_dt"),
                    Job.plan_fin_cost.label("plan_fin_cost"),
                    Job.plan_dev_dt.label("plan_dev_dt"),
                    Job.plan_dev_cost.label("plan_dev_cost"),
                    Job.note.label("note")
                )
                .outerjoin(
                    Company,
                    Company.id == BusinessPlanStr.company
                )
                .outerjoin(
                    ProjectStage,
                    ProjectStage.id == BusinessPlanStr.stage
                )
                .outerjoin(
                    BusinessPlanFacility,
                    BusinessPlanFacility.id == BusinessPlanStr.bpfacility
                )
                .outerjoin(
                    BusinessPlanCostItem,
                    BusinessPlanCostItem.id == BusinessPlanStr.costitem
                )
                .outerjoin(
                    Job,
                    Job.bpstr == BusinessPlanStr.id
                )
                .filter(
                    BusinessPlanStr.businessplan == busplan_id
                )
                .order_by(
                    BusinessPlanStr.id,
                    Job.dt_start,
                    Job.id
                )
                .all()
            )
    
            result = []
            previous_bpstr_id = None
    
            for row in rows:
    
                data = row._mapping
    
                bpstr_id = data["bpstr_id"]
                same_bpstr = bpstr_id == previous_bpstr_id
    
                result.append({
                    # Служебные ID — нужны UI для определения выбранной записи
                    "bpstr_id": bpstr_id,
                    "company_id": data["company_id"],
                    "job_id": data["job_id"],
    
                    # Данные строки бизнес-плана
                    "ID БП": "" if same_bpstr else bpstr_id,
                    "Компания": "" if same_bpstr else data["company_name"],
                    "Этап": "" if same_bpstr else data["stage_name"],
                    "Объект": "" if same_bpstr else data["facility_name"],
                    "Статья затрат": "" if same_bpstr else data["costitem_name"],
    
                    # Данные Job
                    "ID оплаты": data["job_id"] if data["job_id"] else "—",
                    "Начало работ": data["dt_start"],
                    "Завершение работ": data["dt_end"],
                    "Дата финансирования": data["plan_fin_dt"],
                    "Сумма финансирования": data["plan_fin_cost"],
                    "Дата освоения": data["plan_dev_dt"],
                    "Сумма освоения": data["plan_dev_cost"],
                    "Примечание": data["note"]
                })
    
                previous_bpstr_id = bpstr_id
    
            return result



    # =========================================================
    # 2. ПОЛУЧЕНИЕ ДАННЫХ ДЛЯ ФОРМ
    # =========================================================

    @staticmethod
    def get_form_options(project_id=None):
        """
        Получить справочники для заполнения форм.

        Формат списков: [(id, name), ...]
        """

        with SessionLocal() as db:

            companies = (
                db.query(Company.id, Company.name)
                .order_by(Company.name)
                .all()
            )

            facilities = (
                db.query(
                    BusinessPlanFacility.id,
                    BusinessPlanFacility.name
                )
                .order_by(BusinessPlanFacility.name)
                .all()
            )

            costitems = (
                db.query(
                    BusinessPlanCostItem.id,
                    BusinessPlanCostItem.name
                )
                .order_by(BusinessPlanCostItem.name)
                .all()
            )

            stages = (
                db.query(
                    ProjectStage.id,
                    ProjectStage.name
                )
                .order_by(ProjectStage.name)
                .all()
            )

            employees = (
                db.query(Employee.id, Employee.login)
                .order_by(Employee.id)
                .all()
            )

            return {
                "companies": companies,
                "facilities": facilities,
                "costitems": costitems,
                "stages": stages,
                "employees": employees,
            }

    # =========================================================
    # 3. СОЗДАНИЕ СТРОКИ БИЗНЕС-ПЛАНА
    # =========================================================

    @staticmethod
    def db_busplanstr_insert(
        businessplan_id,
        company_id,
        facility_id,
        costitem_id,
        stage_id,
    ):
        """
        Создать только строку бизнес-плана.

        Job и Task здесь не создаются.
        """

        with SessionLocal() as db:

            try:

                bpstr = BusinessPlanStr(
                    businessplan=businessplan_id,
                    company=company_id,
                    bpfacility=facility_id,
                    costitem=costitem_id,
                    stage=stage_id,
                )

                db.add(bpstr)
                db.commit()

                return True, (
                    f"Строка бизнес-плана № {bpstr.id} успешно создана."
                )

            except Exception as e:

                db.rollback()

                return False, (
                    f"Ошибка при создании строки бизнес-плана: {e}"
                )

    # =========================================================
    # 4. СОЗДАНИЕ JOB И TASK
    # =========================================================

    @staticmethod
    def db_job_task_insert(
        bpstr_id,

        # Данные Job
        dt_start=None,
        dt_end=None,
        plan_fin_dt=None,
        plan_fin_cost=None,
        plan_dev_dt=None,
        plan_dev_cost=None,

        # Данные Task
        task_name=None,
        task_desc=None,
        employee_created=None,
        employee_responsible=None,
        importance=None,
        doc=None,

        # Области задачи
        companies=None,
        licenses=None,
        divisions=None,
        facilities=None,
        projects=None,
    ):
        """
        Создать Job и связанную с ним Task.

        Последовательность:
        1. Получаем существующую строку BusinessPlanStr.
        2. Создаём Job и связываем его со строкой БП.
        3. Получаем ID Job.
        4. Создаём Task и связываем её с Job.
        5. Добавляем области задачи.
        6. Сохраняем всё одной транзакцией.
        """

        companies = companies or []
        licenses = licenses or []
        divisions = divisions or []
        facilities = facilities or []
        projects = projects or []

        with SessionLocal() as db:

            try:

                # -------------------------------------------------
                # 1. Проверяем существование строки БП
                # -------------------------------------------------

                bpstr = (
                    db.query(BusinessPlanStr)
                    .filter(BusinessPlanStr.id == bpstr_id)
                    .one_or_none()
                )

                if bpstr is None:
                    raise ValueError(
                        f"Строка бизнес-плана № {bpstr_id} не найдена."
                    )

                # -------------------------------------------------
                # 2. Создаём Job
                # -------------------------------------------------

                job = Job(
                    bpstr=bpstr.id,
                    dt_start=dt_start,
                    dt_end=dt_end,
                    plan_fin_dt=plan_fin_dt,
                    plan_fin_cost=plan_fin_cost,
                    plan_dev_dt=plan_dev_dt,
                    plan_dev_cost=plan_dev_cost,
                )

                db.add(job)
                db.flush()

                # -------------------------------------------------
                # 3. Создаём Task
                # -------------------------------------------------

                task = Task(
                    name=task_name,
                    desc=task_desc,
                    employee_created=employee_created,
                    employee_responsible=employee_responsible,
                    importance=importance,
                    status=TaskStatusEnum.NOT_STARTED,
                    doc=doc,
                    job=job.id,
                )

                db.add(task)
                db.flush()

                # -------------------------------------------------
                # 4. Добавляем компании
                # -------------------------------------------------

                for company in companies:
                    task.companies.append(company)

                # -------------------------------------------------
                # 5. Добавляем лицензии
                # -------------------------------------------------

                for license in licenses:
                    task.licenses.append(license)

                # -------------------------------------------------
                # 6. Добавляем проекты
                # -------------------------------------------------

                for project in projects:
                    task.projects.append(project)

                # -------------------------------------------------
                # 7. Добавляем подразделения
                # -------------------------------------------------

                for division in divisions:

                    division_obj = db.get(
                        Division,
                        division[0]
                    )

                    if division_obj:
                        task.divisions.append(division_obj)

                # -------------------------------------------------
                # 8. Добавляем объекты
                # -------------------------------------------------

                for facility in facilities:

                    facility_obj = db.get(
                        Facility,
                        facility[0]
                    )

                    if facility_obj:
                        task.facilities.append(facility_obj)

                # -------------------------------------------------
                # 9. Сохраняем Job, Task и области
                # -------------------------------------------------
                # # 9. Создаём плановые даты задачи

                pds = PlanDateStart(
                    task=task.id,
                    dt_start=dt_start,
                    employee_created=employee_created
                )
    
                pde = PlanDateEnd(
                    task=task.id,
                    dt_end=dt_end,
                    employee_created=employee_created
                )
    
                db.add_all([pds, pde])
    
                # 10. Создаём плановую стоимость задачи
    
                if (
                    plan_fin_cost is not None
                    and plan_dev_cost is not None
                    and (plan_fin_cost > 0 or plan_dev_cost > 0)
                ):
                    pc = PlanCost(
                        task=task.id,
                        plan_fin_dt=plan_fin_dt,
                        plan_fin_cost=plan_fin_cost,
                        plan_dev_dt=plan_dev_dt,
                        plan_dev_cost=plan_dev_cost
                    )
    
                    db.add(pc)
    
                # 11. Сохраняем все записи одной транзакцией
    
                db.commit()

                return True, (
                    f"Сроки и оплата № {job.id} "
                    f"и задача № {task.id} успешно созданы."
                )

            except Exception as e:

                db.rollback()

                return False, (
                    f"Ошибка при создании сроков, оплаты и задачи: {e}"
                )
