from typing import List
import pandas as pd
from models import SessionLocal, BusinessPlan, Project, BusinessPlanStr, Job, Task, TaskStatusEnum
from datetime import date
from sqlalchemy import inspect as sa_inspect


class ServiceBusplan():
    """Сервис работы с Бизнес-планами"""

    @staticmethod
    def get_dataframe(switch_actual, project_name=None):
        db = SessionLocal()
        try:
            if project_name:
                project = db.query(Project).filter_by(name=project_name).one_or_none()
                if switch_actual:
                    busplans = db.query(BusinessPlan).filter(BusinessPlan.actual==switch_actual, BusinessPlan.project==project.id).all()
                else:
                    busplans = db.query(BusinessPlan).filter(BusinessPlan.project==project.id).all()
            else:
                if switch_actual:
                    busplans = db.query(BusinessPlan).filter_by(actual=switch_actual).all()
                else:
                    busplans = db.query(BusinessPlan).all()
                
            busplans_data = [
                {'ID': c.id,
                 'name': c.name,
                 'date': c.date,
                 'project': (db.query(Project).filter_by(id=c.project).one_or_none().name if c.project else None),
                 'parent': (f"({c.parent}) {db.query(BusinessPlan).filter_by(id=c.parent).one_or_none().name}" if c.parent else None),
                 'actual': c.actual
                }
                for c in busplans]
            data_frame = pd.DataFrame(busplans_data)
            return True, data_frame
        except Exception as e:
            print(f'Ошибка получения бизнес-планов: {e}')
            return False, None
        finally:
            db.close()

    @staticmethod
    def get_busplans(busplans_selected):
        """Список актуальных Бизнес-планов"""
        db = SessionLocal()
        busplans_selected_new = []
        try:
            busplans = db.query(BusinessPlan).filter_by(actual=True).all()
            if len(busplans_selected) > 0:
                for bp in busplans:
                    for bp_s in busplans_selected:
                        if bp_s == bp.id:
                            busplans_selected_new.append(bp)
                return busplans_selected_new, busplans
            else:
                return [], busplans
        except Exception as e:
            print(f'Ошибка получения списка Бизнес-планов: {e}')
            return [], []
        finally:
            db.close()

    @staticmethod
    def get_busplan__id(id: int) -> BusinessPlan:
        """Получение Бизнес-плана по его ID"""
        db = SessionLocal()
        try:
            return db.query(BusinessPlan).filter_by(id=id).one_or_none()
        except Exception as e:
            print(f'Ошибка получения Бизнес-плана по ID: {e}')
            return None
        finally:
            db.close()

    @staticmethod
    def get_busplan_names() -> List[str] | None:
        """Список имен актуальных Бизнес-планов"""
        db = SessionLocal()
        try:
            busplans = db.query(BusinessPlan).filter_by(actual=True).all()
        except Exception as e:
            print(f'Ошибка получения Бизнес-планов по ID: {e}')
        finally:
            db.close()

        # Преобразую данные в плоский список
        busplan_names = [busplan.name for busplan in busplans]
        # Добавляю пустой вариант для возможности пустого выбора
        busplan_names.insert(0, '')
        return busplan_names

    @staticmethod
    def db_busplan_insert(parent_name: str, name: str, date, project_name, note: str, doc: str) -> tuple[bool, str]:
        """Добавление нового Бизнес-плана в базу данных"""
        db = SessionLocal()
        try:
            # Предварительная проверка на существование заводимой Компании
            bp_name = db.query(BusinessPlan).filter_by(name=name).one_or_none()
            if bp_name:
                return False, '❌ Такой Бизнес-план уже существует'
            # Если такой Компании не существует стандартное добавление
            proj = db.query(Project).filter_by(name=project_name).one_or_none()
            bp = BusinessPlan(name=name,
                              date=date,
                              project=proj.id,
                              note=note,
                              doc=doc,
                              actual=True)
            db.add(bp)
            db.commit()
            
            if parent_name:
                busplan_parent = db.query(BusinessPlan).filter_by(name=parent_name).one_or_none()
                bp.parent = busplan_parent.id
            else:
                bp.parent = None
            db.commit()

            return True, '✅ Бизнес-план успешно добавлен!'
        except Exception as e:
            db.rollback()
            print(f'Ошибка добавления Бизнес-плана: {e}')
            return False, '❌ Ошибка при добавлении Бизнес-плана'
        finally:
            db.close()

    @staticmethod
    def db_busplan_update(parent_name: str, busplan_id: int, name: str, date, project_name, note: str, doc: str, actual: bool) -> tuple[bool, str]:
        """Обновление данных Бизнес-плана в базе данных"""
        db = SessionLocal()
        try:
            # Особенность: для обновления данных, обновляемый объект должен быть получен
            # в рамках данной сессии. Если объект получить в другой сессии, а сюда
            # просто передать, то обновление данных в БД не произойдет!
            busplan = db.query(BusinessPlan).filter_by(id=busplan_id).one_or_none()
            # Предварительная проверка на существование Компании при обновлении наименования
            bp_name = db.query(BusinessPlan).filter_by(name=name).one_or_none()
            if bp_name != None:
                if bp_name.id == busplan.id:
                    bp_name = None          
                if (bp_name != None):
                    return False, '❌ Такой Бизнес-план уже существует'
            # Если такой Компании не существует стандартное обновление            
            busplan.name = name
            busplan.date = date
            proj = db.query(Project).filter_by(name=project_name).one_or_none()
            busplan.project = proj.id
            busplan.note = note
            busplan.doc = doc
            busplan.actual = actual

            if parent_name:
                busplan_parent = db.query(BusinessPlan).filter_by(name=parent_name).one_or_none()
                busplan.parent = busplan_parent.id
            else:
                busplan.parent = None

            db.commit()
            
            return True, '✅ Данные по Бизнес-плану успешно обновлены!'
        except Exception as e:
            db.rollback()
            print(f'Ошибка обновления данных Бизнес-плана: {e}')
            return False, '❌ Ошибка при обновлении данных Бизнес-плана'
        finally:
            db.close()

    @staticmethod
    def get_busplans__names(busplans_names):
        """Получение списка Бизнес-планов по их именам"""
        db = SessionLocal()
        try:
            return  db.query(BusinessPlan).filter(BusinessPlan.name.in_(busplans_names)).all()
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения списка Бизнес-планов по их именам: {e}')
            return []
        finally:
            db.close()
            
    @staticmethod
    def get_busplan_names_by_project(project_name):
        """Получение списка Бизнес-планов по иимени проекта"""
        db = SessionLocal()
        try:
            project_id = db.query(Project).filter_by(name=project_name).one_or_none().id
            busplans = db.query(BusinessPlan).filter_by(project=project_id).all()
            busplan_names = [busplan.name for busplan in busplans]
            busplan_names.insert(0, '')
            return busplan_names
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения списка Бизнес-планов по их именам: {e}')
            return []
        finally:
            db.close()    

    @staticmethod
    def get_task_values(source_row_id: int):
    
        db = SessionLocal()
    
        try:
            # Получаем все Job исходной строки
            jobs = (
                db.query(Job)
                .filter(Job.bpstr == source_row_id)
                .all()
            )
    
            job_ids = [job.id for job in jobs]
    
            if not job_ids:
                return None
    
            # Получаем все задачи этих Job
            tasks = (
                db.query(Task)
                .filter(Task.job.in_(job_ids))
                .all()
            )
    
            if not tasks:
                return None
    
            # Фактические даты
            fact_fin_dt = [
                task.fact_fin_dt for task in tasks
                if task.fact_fin_dt is not None
            ]
    
            fact_dev_dt = [
                task.fact_dev_dt for task in tasks
                if task.fact_dev_dt is not None
            ]
    
            # Фактические суммы
            fact_fin_cost = [
                task.fact_fin_cost for task in tasks
                if task.fact_fin_cost is not None
            ]
    
            fact_dev_cost = [
                task.fact_dev_cost for task in tasks
                if task.fact_dev_cost is not None
            ]
    
            # Примечания задач
            notes = [
                f"{task.name}: {task.note}"
                for task in tasks
                if task.note
            ]
    
            return {
                "plan_fin_dt": max(fact_fin_dt) if fact_fin_dt else None,
                "plan_fin_cost": sum(fact_fin_cost) if fact_fin_cost else None,
                "plan_dev_dt": max(fact_dev_dt) if fact_dev_dt else None,
                "plan_dev_cost": sum(fact_dev_cost) if fact_dev_cost else None,
                "notes": notes
            }
    
        finally:
            db.close()



   
    
    @staticmethod
    def form_monitoring(source_bp_id):

        db = SessionLocal()

        try:
            # Получаем исходный бизнес-план
            source_bp = db.query(BusinessPlan).filter(
                BusinessPlan.id == source_bp_id
            ).first()
            # source_bp = db.query(BusinessPlan).filter(
            #     BusinessPlan.id == bp.parent
            # ).first()

            if not source_bp:
                raise ValueError("Исходный бизнес-план не найден")

            # Создаём новый бизнес-план — мониторинг
            monitoring_bp = BusinessPlan(
                name=f"Мониторинг: {source_bp.name}",
                date=date.today(),
                project=source_bp.project,
                doc=source_bp.doc,
                parent=source_bp.id
            )

            db.add(monitoring_bp)
            db.flush()

            # Получаем все строки исходного бизнес-плана
            source_rows = db.query(BusinessPlanStr).filter(
                BusinessPlanStr.businessplan == source_bp.id
            ).all()

            # Обрабатываем каждую строку
            for source_row in source_rows:

                # Создаём строку мониторинга
                monitoring_row = BusinessPlanStr(
                    businessplan=monitoring_bp.id,
                    source_id=source_row.id,

                    company=source_row.company,
                    bpfacility=source_row.bpfacility,
                    costitem=source_row.costitem,
                    stage=source_row.stage,

                    note=source_row.note,
                    actual=source_row.actual
                )

                db.add(monitoring_row)
                db.flush()

                # Получаем все Job, привязанные к исходной строке
                source_jobs = db.query(Job).filter(
                    Job.bpstr == source_row.id
                ).all()

                # Обрабатываем каждый Job отдельно
                for source_job in source_jobs:

                    # Получаем все задачи, связанные с Job
                    tasks = db.query(Task).filter(
                        Task.job == source_job.id
                    ).all()

                    # Фактические даты и суммы финансирования
                    fact_fin_dt = [
                        task.fact_fin_dt
                        for task in tasks
                        if task.fact_fin_dt is not None
                    ]

                    fact_fin_cost = [
                        task.fact_fin_cost
                        for task in tasks
                        if task.fact_fin_cost is not None
                    ]

                    # Фактические даты и суммы освоения
                    fact_dev_dt = [
                        task.fact_dev_dt
                        for task in tasks
                        if task.fact_dev_dt is not None
                    ]

                    fact_dev_cost = [
                        task.fact_dev_cost
                        for task in tasks
                        if task.fact_dev_cost is not None
                    ]

                    # Определяем значения для мониторинга
                    
                    # Финансовые даты
                    plan_fin_dt = (
                        max(fact_fin_dt)
                        if fact_fin_dt
                        else source_job.plan_fin_dt
                    )
                    # Даты освоения
                    plan_dev_dt = (
                        max(fact_dev_dt)
                        if fact_dev_dt
                        else source_job.plan_dev_dt
                    )
                    
                    # Финансовая сумма
                    if fact_fin_cost:
                        plan_fin_cost = sum(fact_fin_cost)
                        plan_dev_cost = sum(fact_dev_cost)
                    elif any(
                        task.status == TaskStatusEnum.CANCELED
                        and task.fact_fin_cost is None
                        for task in tasks
                    ):
                        plan_fin_cost = 0
                        plan_dev_cost = 0
                        plan_fin_dt = None
                        plan_dev_dt = None
                    else:
                        plan_fin_cost = source_job.plan_fin_cost
                        plan_dev_cost = source_job.plan_dev_cost
                    

                    task = db.query(Task).filter(Task.job == source_job.id).first()
                    # Создаём копию Job для мониторинга
                    monitoring_job = Job(
                        bpstr=monitoring_row.id,

                        dt_start=source_job.dt_start,
                        dt_end=source_job.dt_end,

                        plan_fin_dt=plan_fin_dt,
                        plan_fin_cost=plan_fin_cost,

                        plan_dev_dt=plan_dev_dt,
                        plan_dev_cost=plan_dev_cost,

                        note=task.note if task else None,
                        actual=source_job.actual
                    )

                    db.add(monitoring_job)

            db.commit()

            return monitoring_bp.id

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()



    def get_monitoring_tasks(monitoring_row_id: int):
    
        db = SessionLocal()
    
        try:
            monitoring_row = (
                db.query(BusinessPlanStr)
                .filter(BusinessPlanStr.id == monitoring_row_id)
                .one_or_none()
            )
        
            if monitoring_row is None or monitoring_row.source_id is None:
                return []
        
            jobs = (
                db.query(Job)
                .filter(Job.bpstr == monitoring_row.source_id)
                .all()
            )
        
            job_ids = [job.id for job in jobs]
        
            if not job_ids:
                return []
        
            return (
                db.query(Task)
                .filter(Task.job.in_(job_ids))
                .all()
            )
    
        except Exception:
            db.rollback()
            raise
    
        finally:
            db.close()    
