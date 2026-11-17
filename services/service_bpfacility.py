from typing import List
import pandas as pd
from models import SessionLocal, BusinessPlanFacility, Project


class ServiceBPFacility():
    """Сервис работы с Объектами из Бизнес-плана"""

    @staticmethod
    def get_dataframe(switch_actual, project_name):
        db = SessionLocal()
        try:
            if project_name:
                project = db.query(Project).filter_by(name=project_name).one_or_none()
                if switch_actual:
                    bpfacilities = db.query(BusinessPlanFacility).filter_by(actual=switch_actual, project=project.id).all()
                else:
                    bpfacilities = db.query(BusinessPlanFacility).filter_by(project=project.id).all()
            else:
                if switch_actual:
                    bpfacilities = db.query(BusinessPlanFacility).filter_by(actual=switch_actual).all()
                else:
                    bpfacilities = db.query(BusinessPlanFacility).all()
           
            bpfacilities_data = [
                {'ID': c.id,
                 'name': c.name,
                 'project': c.project_back.name,
                 'count': c.count,
                 'length': c.length,
                 'square': c.square,
                 'actual': c.actual
                }
                for c in bpfacilities]
            data_frame = pd.DataFrame(bpfacilities_data)
            return True, data_frame
        except Exception as e:
            print(f'Ошибка получения статей затрат: {e}')
            return False, None
        finally:
            db.close()

    # @staticmethod
    # def get_busplans(busplans_selected):
    #     """Список актуальных этапов проектов"""
    #     db = SessionLocal()
    #     busplans_selected_new = []
    #     try:
    #         busplans = db.query(BusinessPlan).filter_by(actual=True).all()
    #         if len(busplans_selected) > 0:
    #             for bp in busplans:
    #                 for bp_s in busplans_selected:
    #                     if bp_s == bp.id:
    #                         busplans_selected_new.append(bp)
    #             return busplans_selected_new, busplans
    #         else:
    #             return [], busplans
    #     except Exception as e:
    #         print(f'Ошибка получения списка Бизнес-планов: {e}')
    #         return [], []
    #     finally:
    #         db.close()

    @staticmethod
    def get_bpfacility__id(id: int) -> BusinessPlanFacility:
        """Получение Объекта из Бизнес-плана по его ID"""
        db = SessionLocal()
        try:
            return db.query(BusinessPlanFacility).filter_by(id=id).one_or_none()
        except Exception as e:
            print(f'Ошибка получения Объекта из Бизнес-плана по ID: {e}')
            return None
        finally:
            db.close()

    # @staticmethod
    # def get_busplan_names() -> List[str] | None:
    #     """Список имен актуальных Бизнес-планов"""
    #     db = SessionLocal()
    #     try:
    #         busplans = db.query(BusinessPlan).filter_by(actual=True).all()
    #     except Exception as e:
    #         print(f'Ошибка получения Бизнес-планов по ID: {e}')
    #     finally:
    #         db.close()

    #     # Преобразую данные в плоский список
    #     busplan_names = [busplan.name for busplan in busplans]
    #     # Добавляю пустой вариант для возможности пустого выбора
    #     busplan_names.insert(0, '')
    #     return busplan_names

    @staticmethod
    def db_bpfacility_insert(name: str, project_name, count, length, square) -> tuple[bool, str]:
        """Добавление нового объекта из бизнес-плана в базу данных"""
        db = SessionLocal()
        try:
            # Предварительная проверка на существование заводимого Этапа проекта
            bpfacility_name = db.query(BusinessPlanFacility).filter_by(name=name).one_or_none()
            if bpfacility_name:
                return False, '❌ Такой объект в Бизнес-плане уже существует'
            # Если такой Компании не существует стандартное добавление
            project = db.query(Project).filter_by(name=project_name).one_or_none()
            bpfacility = BusinessPlanFacility(name=name,
                                              project=project.id,
                                              count=count,
                                              length=length,
                                              square=square,
                                              actual=True)
            db.add(bpfacility)
            db.commit()
            return True, '✅ Объект из Бизнес-плана успешно добавлена!'
        except Exception as e:
            db.rollback()
            print(f'Ошибка добавления Статьи затрат: {e}')
            return False, '❌ Ошибка при добавлении Объекта из Бизнес-плана'
        finally:
            db.close()

    @staticmethod
    def db_bpfacility_update(bpfacility_id: int, name: str, project_name, count, length, square, note: str, actual: bool) -> tuple[bool, str]:
        """Обновление данных объекта из бизнес-плана в базе данных"""
        db = SessionLocal()
        try:
            # Особенность: для обновления данных, обновляемый объект должен быть получен
            # в рамках данной сессии. Если объект получить в другой сессии, а сюда
            # просто передать, то обновление данных в БД не произойдет!
            bpfacility = db.query(BusinessPlanFacility).filter_by(id=bpfacility_id).one_or_none()
            # Предварительная проверка на существование Компании при обновлении наименования
            bpfacility_name = db.query(BusinessPlanFacility).filter_by(name=name).one_or_none()
            if bpfacility_name:
                if bpfacility_name.id == bpfacility.id:
                    bpfacility_name = None          
            if (bpfacility_name != None):
                return False, '❌ Такой объект из бизнес-плана уже существует'
            # Если такой Компании не существует стандартное обновление            
            bpfacility.name = name
            
            project = db.query(Project).filter_by(name=project_name).one_or_none()
            bpfacility.project = project.id

            bpfacility.count = count
            bpfacility.length = length
            bpfacility.square = square
            bpfacility.note = note
            bpfacility.actual = actual
            db.commit()
            return True, '✅ Данные по объекту из бизнес-плана успешно обновлены!'
        except Exception as e:
            db.rollback()
            print(f'Ошибка обновления данных объекта из бизнес-плана: {e}')
            return False, '❌ Ошибка при обновлении данных объекта из бизнес-плана'
        finally:
            db.close()

    # @staticmethod
    # def get_busplans__names(busplans_names):
    #     """Получение списка Бизнес-планов по их именам"""
    #     db = SessionLocal()
    #     try:
    #         return  db.query(BusinessPlan).filter(BusinessPlan.name.in_(busplans_names)).all()
    #     except Exception as e:
    #         db.rollback()
    #         print(f'Ошибка получения списка Бизнес-планов по их именам: {e}')
    #         return []
    #     finally:
    #         db.close()