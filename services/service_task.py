from datetime import date
from typing import List
from models import SessionLocal, Task, Employee, TaskStatusEnum, TaskImportanceEnum, Company, PlanDateStart, PlanDateEnd, PlanCost, License, Division, Project, Facility, Permission
from sqlalchemy import or_


class ServiceTask():
    """Сервис работы с задачами"""

    @staticmethod
    def get_relation_from_object(obj) -> str:
        """Получение наименования поля в задаче, по типу объекта"""
        db = SessionLocal()
        relation = {
                    'companies': [],
                    'licenses': [],
                    'facilities': [],
                    'divisions': [],
                    'projects': []
                }
        try:
            if obj.__class__.__name__ == "Company":
                relation['companies'].append(obj.id)
            if obj.__class__.__name__ == "Division":
                relation['divisions'].append(obj.id)
                company = db.query(Company).filter_by(id=obj.company).one_or_none()
                relation['companies'].append(company.id)
            if obj.__class__.__name__ == "License":
                relation['licenses'].append(obj.id)
                company = db.query(Company).filter_by(id=obj.company).one_or_none()
                relation['companies'].append(company.id)
            if obj.__class__.__name__ == "Project":
                relation['projects'].append(obj.id)
                division = db.query(Division).filter_by(id=obj.division).one_or_none()
                relation['divisions'].append(division.id)
                company = db.query(Company).filter_by(id=division.company).one_or_none()
                relation['companies'].append(company.id)
            if obj.__class__.__name__ == "Facility":
                relation['facilities'].append(obj.id)
                license = db.query(License).filter_by(id=obj.license).one_or_none()
                relation['licenses'].append(license.id)
                company = db.query(Company).filter_by(id=license.company).one_or_none()
                relation['companies'].append(company.id)

        except Exception as e:
            print(f'Ошибка получения relation: {e}')
        finally:
            db.close()

        return relation

    @staticmethod
    def get_field_from_object(obj) -> str:
        """Получение наименования поля в задаче, по типу объекта"""
        if obj.__class__.__name__ == "Company":
            return 'companies'
        if obj.__class__.__name__ == "Division":
            return 'divisions'
        if obj.__class__.__name__ == "License":
            return 'licenses'
        if obj.__class__.__name__ == "Project":
            return 'projects'
        if obj.__class__.__name__ == "Facility":
            return 'facilities'

    
    @staticmethod
    def get_employee_names():
        """Получение списка сотрудников"""
        db = SessionLocal()
        employeies = []
        try:
            employeies = db.query(Employee).filter_by(actual=True).all()
        except Exception as e:
            print(f'Ошибка получения списка сотрудников: {e}')
        finally:
            db.close()
        employee_names_list = []
        for employee in employeies:
            employee_names_list.append(f'({employee.id}): {employee.surname} {employee.name[0]}. {employee.patronymic[0]}.')
        employee_names_list.insert(0, '')
        return employee_names_list

    @staticmethod
    def get_employee_names_index(employee_names_list, id):
        """Получение индекса Пользователя по его ID"""
        for i, name in enumerate(employee_names_list):
            if int(name.split(':')[0][1:-1]) == id:
                return i

    @staticmethod
    def get_index__importance_status(task_importance, task_status):
        """Индексы Важности и Статуса"""
        importances = [
            TaskImportanceEnum.LOW.value,
            TaskImportanceEnum.MIDDLE.value,
            TaskImportanceEnum.HIGH.value
        ]
        statuses = [
            TaskStatusEnum.NOT_STARTED.value,
            TaskStatusEnum.WORKED.value,
            TaskStatusEnum.CANCELED.value,
            TaskStatusEnum.ENDED.value
        ]
        index_importance = importances.index(task_importance)
        index_status = statuses.index(task_status)
        return index_importance, index_status

    @staticmethod
    def task_cont_children(task, count=0, count_all=0):
        """Количество не завершенных подзадач"""
        children = ServiceTask.get_task_children_count(task, False)
        if len(children) > 0:
            for child in children:
                count_all += 1
                if (child.actual == True) and ((child.status == TaskStatusEnum.NOT_STARTED) or (child.status == TaskStatusEnum.WORKED)):
                    count += 1
                    ServiceTask.task_cont_children(child, count)
        return count, count_all

    @staticmethod
    def get_task_plane__start_end_costs(task_id):
        """
        Получение дат начала и завершения задачи,
        плановых показателей: дата финансирования, величина финансирования, дата освоения, величина освоения
        """
        db = SessionLocal()
        try:
            dt_start = db.query(PlanDateStart).filter(PlanDateStart.task==task_id, PlanDateStart.actual==True).order_by(PlanDateStart.id.desc()).first().dt_start
            dt_end = db.query(PlanDateEnd).filter(PlanDateEnd.task==task_id, PlanDateEnd.actual==True).order_by(PlanDateEnd.id.desc()).first().dt_end
            p_cost = db.query(PlanCost).filter(PlanCost.task==task_id, PlanCost.actual==True).order_by(PlanCost.id.desc()).first()
            if p_cost != None:
                p_f_dt = p_cost.plan_fin_dt
                p_f_ct = p_cost.plan_fin_cost
                p_d_dt = p_cost.plan_dev_dt
                p_d_ct = p_cost.plan_dev_cost
                p_nds = p_cost.nds
                p_ndfl = p_cost.ndfl
                return dt_start, dt_end, p_f_dt, p_f_ct, p_d_dt, p_d_ct, p_nds, p_ndfl
            else:
                return dt_start, dt_end, None, None, None, None, None, None
        except Exception as e:
            print(f'Ошибка получения плановых дат и платежей: {e}')
            return None, None, None, None, None, None, None, None
        finally:
            db.close()

    @staticmethod
    def get_task__importance(importance):
        if importance == 'LOW':
            return '⚫', 'gray'
        if importance == 'MIDDLE':
            return '🔵', 'blue'
        if importance == 'HIGH':
            return '🔴', 'red'

    @staticmethod
    def db_task_insert(user_id, name: str, desc: str, responsible: str, importance: str, dt_start, dt_end, doc=None, plan_fin_dt=None, plan_fin_cost=None, plan_dev_dt=None, plan_dev_cost=None, nds=None, ndfl=None,
                       parent_id=None, companies=None, divisions=None, licenses=None, projects=None, facilities=None) -> tuple[bool, str]:
        """Сохранение задачи"""
        if name == '' or name == None: return False, 'Задача не определена'
        if desc == '' or desc == None: return False, 'Описание задачи не определено'
        if responsible == '' or responsible == None: return False, 'Ответственный не указан'
        if importance == '' or importance == None: return False, 'Не определена важность задачи'
        if dt_start == '' or dt_start == None: return False, 'Не определена дата начала задачи'
        if dt_end == '' or dt_end == None: return False, 'Не определена дата завершения задачи'

        db = SessionLocal()
        try:
            responsible_id = int(responsible.split(':')[0].strip()[1:-1])
            importance = importance.split()[1]  # ['⚫ Низкая', '🔵 Средняя', '🔴 Высокая']
            if importance == 'Низкая':
                importance = TaskImportanceEnum.LOW
            if importance == 'Средняя':
                importance = TaskImportanceEnum.MIDDLE
            if importance == 'Высокая':
                importance = TaskImportanceEnum.HIGH
            task = Task(
                name=name,
                desc=desc,
                parent=parent_id,
                employee_created=user_id,
                employee_responsible=responsible_id,
                importance=importance,
                doc=doc
            )

            if companies:
                if len(companies)>0:
                    for i in companies:
                        task.companies.append(i)

            if divisions:
                if len(divisions)>0:
                    for i in divisions:
                        c = db.query(Division).filter(Division.id==i[0]).one_or_none()
                        task.divisions.append(c)

            if licenses:
                if len(licenses)>0:
                    for i in licenses:
                        task.licenses.append(i)

            if projects:
                if len(projects)>0:
                    for i in projects:
                        task.projects.append(i)

            if facilities:
                if len(facilities)>0:
                    for i in facilities:
                        c = db.query(Facility).filter(Facility.id==i[0]).one_or_none()
                        task.facilities.append(c)

            db.add(task)
            db.commit()
            pds = PlanDateStart(task=task.id, dt_start=dt_start, employee_created=user_id)
            pde = PlanDateEnd(task=task.id, dt_end=dt_end, employee_created=user_id)
            db.add_all([pds, pde])
            db.commit()
            if plan_fin_cost != None and plan_dev_cost != None:
                if plan_fin_cost > 0 or plan_dev_cost > 0:
                    pc = PlanCost(task=task.id,
                                  plan_fin_dt=plan_fin_dt,
                                  plan_fin_cost=plan_fin_cost,
                                  plan_dev_dt=plan_dev_dt,
                                  plan_dev_cost=plan_dev_cost,
                                  nds=nds,
                                  ndfl=ndfl)
                    db.add(pc)
                    db.commit()
            
            return True, 'Задача успешно добавлена'
        except Exception as e:
            print(f'Ошибка добавления задачи: {e}')
            return False, 'Ошибка добавления задачи'
        finally:
            db.close()

    @staticmethod
    def db_task_update(user_id, task_id: int, task_parent: int, name: str, desc: str, responsible, importance: str, status: str, dt_start, dt_end, doc: str, plandatefin, plancostfin, plandatedev, plancostdev, plannds, planndfl, factdatefin, factcostfin, factdatedev, factcostdev, factinfo, note, companies=None, divisions=None, licenses=None, projects=None, facilities=None):
        """Обновление задачи"""
        if name == '' or name == None: return False, 'Задача не определена'
        if desc == '' or desc == None: return False, 'Описание задачи не определено'
        if responsible == '' or responsible == None: return False, 'Ответственный не указан'
        if importance == '' or importance == None: return False, 'Не определена важность задачи'
        if dt_start == '' or dt_start == None: return False, 'Не определена дата начала задачи'
        if dt_end == '' or dt_end == None: return False, 'Не определена дата завершения задачи'
            
        db = SessionLocal()
        task = db.query(Task).filter_by(id=task_id).one_or_none()
        try:
            responsible_id = int(responsible.split(':')[0].strip()[1:-1])
            importance = importance.split()[1]  # ['⚫ Низкая', '🔵 Средняя', '🔴 Высокая']
            if importance == 'Низкая':
                importance = TaskImportanceEnum.LOW
            if importance == 'Средняя':
                importance = TaskImportanceEnum.MIDDLE
            if importance == 'Высокая':
                importance = TaskImportanceEnum.HIGH
            # ['🧘‍♂️ Не начата', '👨‍🔧 В работе', '🙅‍♂️ Отменена', '💃 Завершена']
            if status == '🧘‍♂️ Не начата':
                status = TaskStatusEnum.NOT_STARTED
                task.employee_ended = None
                task.dt_ended = None
                task.actual = True
            if status == '👨‍🔧 В работе':
                status = TaskStatusEnum.WORKED
                task.employee_ended = None
                task.dt_ended = None
                task.actual = True
            if status == '🙅‍♂️ Отменена':
                status = TaskStatusEnum.CANCELED
                task.employee_ended = user_id
                task.dt_ended = date.today()
                task.actual = False
            if status == '💃 Завершена':
                status = TaskStatusEnum.ENDED
                task.employee_ended = user_id
                task.dt_ended = date.today()
                task.actual = False

            task.parent = task_parent if task_parent else None
            task.name = name
            task.desc = desc
            task.responsible = responsible
            task.importance = importance
            task.status = status
            task.doc = doc
            task.fact_fin_dt = factdatefin
            task.fact_fin_cost = factcostfin
            task.fact_dev_dt = factdatedev
            task.fact_dev_cost = factcostdev
            task.cost_info = factinfo
            task.note = note
            db.commit()

            if companies:
                task.companies.clear()
                for i in companies:
                    c = db.query(Company).filter(Company.id==i.id).one_or_none()
                    task.companies.append(c)
            else:
                task.companies.clear()

            if divisions:
                task.divisions.clear()
                for i in divisions:
                    c = db.query(Division).filter(Division.id==i[0]).one_or_none()
                    task.divisions.append(c)
            else:
                task.divisions.clear()

            if licenses:
                task.licenses.clear()
                for i in licenses:
                    c = db.query(License).filter(License.id==i.id).one_or_none()
                    task.licenses.append(c)
            else:
                task.licenses.clear()

            if projects:
                task.projects.clear()
                for i in projects:
                    c = db.query(Project).filter(Project.id==i.id).one_or_none()
                    task.projects.append(c)
            else:
                task.projects.clear()

            if facilities:
                task.facilities.clear()
                for i in facilities:
                    c = db.query(Facility).filter(Facility.id==i[0]).one_or_none()
                    task.facilities.append(c)
            else:
                task.facilities.clear()

            db.commit()

            # Плановые даты начала и заврешения задачи
            pds = db.query(PlanDateStart).filter_by(task=task.id, actual=True).order_by(PlanDateStart.id.desc()).first()
            if pds:
                if pds.dt_start != dt_start:
                    pds.actual = False
                    pds_new = PlanDateStart(task=task.id, dt_start=dt_start, employee_created=user_id)
                    db.add(pds_new)
                    db.commit()
            else:
                pds_new = PlanDateStart(task=task.id, dt_start=dt_start, employee_created=user_id)
                db.add(pds_new)
                db.commit()
                
            pde = db.query(PlanDateEnd).filter_by(task=task.id, actual=True).order_by(PlanDateEnd.id.desc()).first()
            if pde:
                if pde.dt_end != dt_end:
                    pde.actual = False
                    pde_new = PlanDateEnd(task=task.id, dt_end=dt_end, employee_created=user_id)
                    db.add(pde_new)
                    db.commit()
            else:
                pde_new = PlanDateEnd(task=task.id, dt_end=dt_end, employee_created=user_id)
                db.add(pde_new)
                db.commit()

            # Плановые даты финансирования и освоения, суммы и НДС, НДФЛ
            plancost = db.query(PlanCost).filter_by(task=task.id, actual=True).order_by(PlanCost.id.desc()).first()
            if plancost:
                plan_fin_dt = plancost.plan_fin_dt
                plan_fin_cost = plancost.plan_fin_cost
                plan_dev_dt = plancost.plan_dev_dt
                plan_dev_cost = plancost.plan_dev_cost
                nds = plancost.nds
                ndfl = plancost.ndfl
            else:
                plan_fin_dt = None
                plan_fin_cost = None
                plan_dev_dt = None
                plan_dev_cost = None
                nds = None
                ndfl = None

            if plan_fin_dt != plandatefin or plan_fin_cost != plancostfin or plan_dev_dt != plandatedev or plan_dev_cost != plancostdev or nds != plannds or ndfl != planndfl:
                # plancost_ = plancost.one_or_none()
                if plancost:
                    plancost.actual = False
                if plandatefin == None or plancostfin == 0:
                    plan_fin_dt = None
                    plan_fin_cost = 0.0
                if plandatedev == None or plancostdev == 0:
                    plan_dev_dt = None
                    plan_dev_cost = 0.0
                pc = PlanCost(task=task.id,
                                  plan_fin_dt=plandatefin,
                                  plan_fin_cost=plancostfin,
                                  plan_dev_dt=plandatedev,
                                  plan_dev_cost=plancostdev,
                                  nds=plannds,
                                  ndfl=planndfl)
                db.add(pc)
                db.commit()

            return True, 'Задача успешно отредактирована'
        except Exception as e:
            print(f'Ошибка редактирования задачи: {e}')
            return False, 'Ошибка редактирования задачи'
        finally:
            db.close()


    @staticmethod
    def get_tasks(obj, actual) -> List[Task]:
        """Получение всех задач объекта"""
        db = SessionLocal()
        try:
            field = ServiceTask.get_field_from_object(obj)
            tasks = db.query(Task).filter(getattr(Task, field).any(id=obj.id)).filter(Task.parent.is_(None))
            tasks = tasks.filter(Task.actual==actual).order_by(Task.id.desc()).all() if actual else tasks.all()
            return tasks
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения задач: {e}')
            return None
        finally:
            db.close()

            
    @staticmethod
    def matches(task, filt) -> List[Task]:
        db = SessionLocal()
        try:
            if task is not None:
                if filt is None:
                    return False
                if filt['employees']:
                    if str(task.employee_responsible) not in filt['employees']:
                        return False
                if filt['companies']:
                    if not any(company.id in filt['companies'] for company in task.companies):
                        return False
                if filt['divisions']:
                    if not any(division.id in filt['divisions'] for division in task.divisions):
                        return False
                if filt['licenses']:
                    if not any(license.id in filt['licenses'] for license in task.licenses):
                        return False
                if filt['projects']:
                    if not any(project.id in filt['projects'] for project in task.projects):
                        return False
                if filt['facilities']:
                    if not any(facility.id in filt['facilities'] for facility in task.facilities):
                        return False
                return True
        except Exception as e:
            print(f'Ошибка фильтрации задач на главной странице: {e}')
            return None
        finally:
            db.close()



    @staticmethod
    def get_parent_from_subtasks(subtask):
        db = SessionLocal()
        try:
            subtask = db.query(Task).filter(Task.id == subtask).one_or_none()
            while subtask and subtask.parent is not None:
                subtask = subtask.parent
                subtask = db.query(Task).filter(Task.id == subtask).one_or_none()
            return subtask
        except Exception as e:
            db.rollback()
            print(f'Ошибка get_parent_from_subtasks на главной странице: {e}')
            return None
        finally:
            db.close()        

    
    @staticmethod
    def get_tasks_main_page(filt, actual, cur_emp_id) -> List[Task]:
        """Получение всех задач по фильтру на главной странице"""
        db = SessionLocal()
        try:
            tasks = set()
            tasks_set = set()
            final_tasks = []
            all_tasks = db.query(Task).filter(Task.actual == actual)

            for task in all_tasks:
                if ServiceTask.matches(task, filt):
                    tasks.add(task)

            for task in tasks:
                if task.parent == None:
                    tasks_set.add(task)
                else:
                    head_task = ServiceTask.get_parent_from_subtasks(task.id)
                    if head_task not in tasks_set:
                        tasks_set.add(head_task)
            tasks_ids = []
            for t in tasks_set:
                tasks_ids.append(t.id)
            tasks_ids = set(tasks_ids)
            tasks_ids = list(tasks_ids)
            for t in tasks_ids:
                final_tasks.append(db.query(Task).filter(Task.id == t).one_or_none())
                
            if filt['employees'] is None and filt['companies'] is None and filt['divisions'] is None and filt['licenses'] is None and filt['projects'] is None and filt['facilities'] is None:
                final_tasks = set()
            user_tasks_2 = []
            for t in final_tasks:
                t_emp = db.query(Employee).filter_by(id=t.employee_responsible).one_or_none()
                t_emp_company = db.query(Company).filter_by(id=t_emp.company).one_or_none()
                cur_emp = db.query(Employee).filter_by(id=cur_emp_id).one_or_none()
                cur_emp_company = db.query(Company).filter_by(id=cur_emp.company).one_or_none()
                if cur_emp_company.name != 'ГПН-ГЕО':
                    if t_emp.company==cur_emp.company:
                        user_tasks_2.append(t)
                else:
                    user_tasks_2.append(t)
            return final_tasks
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения задач пользователя на главной странице: {e}')
            return None
        finally:
            db.close()

            
    @staticmethod
    def check_subtasks(task, filt):
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task.id).one_or_none()
            # print(f"Проверяю {task.name} {hash(task)} ответственный {task.employee_responsible}")
    
            # текущая задача подходит
            # print('filter', ServiceTask.matches(task, filt))
            # print('---filt---', filt)
            if ServiceTask.matches(task, filt):
                # print(f"Подошла {task.name}")
                return True
    
            # пока есть подзадачи проверяем их
            children = db.query(Task).filter(Task.parent == task.id).all()
            for child in children:
                # print(f"Спускаюсь из {task.name} в {child.name}")
                if ServiceTask.check_subtasks(child, filt):
                    return True
            return False
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения check_subtasks задач: {e}')
            return None
        finally:
            db.close()
        
    @staticmethod
    def get_task_children(task, actual, filt):
        """Получение дочерних задач у родительской задачи"""
        db = SessionLocal()
        try:
            children = db.query(Task).filter(Task.parent == task.id)
            children = children.filter(Task.actual==actual).all() if actual else children.all()
            children_set = set()
            for child in children:
                if ServiceTask.check_subtasks(child, filt) or ServiceTask.matches(child, filt):
                    children_set.add(child)
            return children_set
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения дочерних задач: {e}')
            return None
        finally:
            db.close()


    
    @staticmethod
    def get_task_children_count(task, actual, filt=None):
        """Получение дочерних задач у родительской задачи"""
        db = SessionLocal()
        try:
            children = db.query(Task).filter(Task.parent == task.id)
            children = children.filter(Task.actual==actual).all() if actual else children.all()
            if filt != None:
                children = (
                    db.query(Task)
                    .filter(Task.parent == task.id,
                            # Task.employee_responsible.in_(filt['employees']) if filt['employees'] else True,
                            Task.companies.any(Company.id.in_(filt['companies'])) if filt['companies'] else True,
                            Task.divisions.any(Division.id.in_(filt['divisions'])) if filt['divisions'] else True,
                            Task.licenses.any(License.id.in_(filt['licenses'])) if filt['licenses'] else True,
                            Task.projects.any(Project.id.in_(filt['projects'])) if filt['projects'] else True,
                            Task.facilities.any(Facility.id.in_(filt['facilities'])) if filt['facilities'] else True,
                            or_(Task.employee_responsible.in_(filt['employees']) if filt['employees'] else True,
                            Task.children.any(Task.employee_responsible.in_(filt['employees'])) if filt['employees'] else False
                            )
                           )
                    )
                children = children.filter(Task.actual==actual).all() if actual else children.all()
                children = set(children)
            return children
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения дочерних комментариев: {e}')
            return None
        finally:
            db.close()

    @staticmethod
    def get_plan_date_end(pk):
        """Получение плановой даты окончания у задачи"""
        db = SessionLocal()
        try:
            plan_date_end = db.query(PlanDateEnd).filter(PlanDateEnd.task == pk, PlanDateEnd.actual == True).one_or_none()
            return plan_date_end
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения плановой даты окончания у задачи: {e}')
            return None
        finally:
                db.close()

    @staticmethod
    def get_task_hub(task):
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id==task.id).one_or_none()
            relation = {
                    'companies': [],
                    'licenses': [],
                    'facilities': [],
                    'divisions': [],
                    'projects': []
                }
            if task.companies:
                for i in task.companies:
                    c = db.query(Company).filter(Company.id == i.id).one_or_none()
                    relation['companies'].append(c.id)
            if task.licenses:
                for i in task.licenses:
                    c = db.query(License).filter(License.id == i.id).one_or_none()
                    relation['licenses'].append(c.id)
            if task.facilities:
                for i in task.facilities:
                    c = db.query(Facility).filter(Facility.id == i.id).one_or_none()
                    relation['facilities'].append(c.id)
            if task.divisions:
                for i in task.divisions:
                    c = db.query(Division).filter(Division.id == i.id).one_or_none()
                    relation['divisions'].append(c.id)
            if task.projects:
                for i in task.projects:
                    c = db.query(Project).filter(Project.id == i.id).one_or_none()
                    relation['projects'].append(c.id)

            return relation
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения связей задачи: {e}')
            return None
        finally:
            db.close()


    @staticmethod
    def allowed_empoyee(emp):
        db = SessionLocal()
        company = db.query(Company).filter_by(id=emp.company).one_or_none()
        return True if company.name == 'ГПН-ГЕО' else False

        
    @staticmethod
    def expanded_tasks(task_id):
        db = SessionLocal()
        expanded_tasks = [task_id]
        try:
            task = db.query(Task).filter(Task.id == task_id).one_or_none()
            while task and task.parent is not None:
                task = task.parent
                task = db.query(Task).filter(Task.id == task).one_or_none()
                expanded_tasks.append(task.id)
            # print('expanded_tasks', expanded_tasks)
            return expanded_tasks
        except Exception as e:
            db.rollback()
            print(f'Ошибка expanded_tasks на главной странице: {e}')
            return None
        finally:
            db.close()

    @staticmethod
    def get_tasks_by_job(job_id):
        db = SessionLocal() 
        try:
            tasks = db.query(Task).filter(Task.job == int(job_id)).all()
            return tasks
        except Exception as e:
            db.rollback()
            print(f'Ошибка get_tasks_by_job: {e}')
            return None
        finally:
            db.close()        