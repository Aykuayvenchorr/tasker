from typing import List
import pandas as pd
from models import SessionLocal, ProjectStage


class ServiceProjectStage():
    """Сервис работы с Этапами проекта"""

    @staticmethod
    def get_dataframe(switch_actual):
        db = SessionLocal()
        try:
            if switch_actual:
                projstages = db.query(ProjectStage).filter_by(actual=switch_actual).all()
            else:
                projstages = db.query(ProjectStage).all()
                
            projstages_data = [
                {'ID': c.id,
                 'name': c.name,
                 'actual': c.actual
                }
                for c in projstages]
            data_frame = pd.DataFrame(projstages_data)
            return True, data_frame
        except Exception as e:
            print(f'Ошибка получения этапов проектов: {e}')
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
    def get_projstage__id(id: int) -> ProjectStage:
        """Получение Бизнес-плана по его ID"""
        db = SessionLocal()
        try:
            return db.query(ProjectStage).filter_by(id=id).one_or_none()
        except Exception as e:
            print(f'Ошибка получения этапа проекта по ID: {e}')
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
    def db_projstage_insert(name: str) -> tuple[bool, str]:
        """Добавление нового Этапа проекта в базу данных"""
        db = SessionLocal()
        try:
            # Предварительная проверка на существование заводимого Этапа проекта
            projstage_name = db.query(ProjectStage).filter_by(name=name).one_or_none()
            if projstage_name:
                return False, '❌ Такой Этап проекта уже существует'
            # Если такой Компании не существует стандартное добавление
            projstage = ProjectStage(name=name,
                                  actual=True)
            db.add(projstage)
            db.commit()
            return True, '✅ Этап проекта успешно добавлен!'
        except Exception as e:
            db.rollback()
            print(f'Ошибка добавления Этапа проекта: {e}')
            return False, '❌ Ошибка при добавлении Этапа проекта'
        finally:
            db.close()

    @staticmethod
    def db_projstage_update(projstage_id: int, name: str, note: str, actual: bool) -> tuple[bool, str]:
        """Обновление данных Этапа проекта в базе данных"""
        db = SessionLocal()
        try:
            # Особенность: для обновления данных, обновляемый объект должен быть получен
            # в рамках данной сессии. Если объект получить в другой сессии, а сюда
            # просто передать, то обновление данных в БД не произойдет!
            projstage = db.query(ProjectStage).filter_by(id=projstage_id).one_or_none()
            # Предварительная проверка на существование Компании при обновлении наименования
            projstage_name = db.query(ProjectStage).filter_by(name=name).one_or_none()
            if projstage_name:
                if projstage_name.id == projstage.id:
                    projstage_name = None          
            if (projstage_name != None):
                return False, '❌ Такой Этап проекта уже существует'
            # Если такой Компании не существует стандартное обновление            
            projstage.name = name
            projstage.note = note
            projstage.actual = actual
            db.commit()
            return True, '✅ Данные по Этапу проекта успешно обновлены!'
        except Exception as e:
            db.rollback()
            print(f'Ошибка обновления данных Этапа проекта: {e}')
            return False, '❌ Ошибка при обновлении данных Этапа проекта'
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