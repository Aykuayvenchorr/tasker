from typing import List
import pandas as pd
from models import SessionLocal, BusinessPlanCostItem


class ServiceBPCostItem():
    """Сервис работы со Статьями затрат"""

    @staticmethod
    def get_dataframe(switch_actual):
        db = SessionLocal()
        try:
            if switch_actual:
                bpcostitems = db.query(BusinessPlanCostItem).filter_by(actual=switch_actual).all()
            else:
                bpcostitems = db.query(BusinessPlanCostItem).all()
                
            bpcostitems_data = [
                {'ID': c.id,
                 'name': c.name,
                 'actual': c.actual
                }
                for c in bpcostitems]
            data_frame = pd.DataFrame(bpcostitems_data)
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
    def get_bpcostitem__id(id: int) -> BusinessPlanCostItem:
        """Получение Статьи затрат по ее ID"""
        db = SessionLocal()
        try:
            return db.query(BusinessPlanCostItem).filter_by(id=id).one_or_none()
        except Exception as e:
            print(f'Ошибка получения Статьи затрат по ID: {e}')
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
    def db_bpcostitem_insert(name: str) -> tuple[bool, str]:
        """Добавление новой Статьи затрат в базу данных"""
        db = SessionLocal()
        try:
            # Предварительная проверка на существование заводимого Этапа проекта
            bpcostitem_name = db.query(BusinessPlanCostItem).filter_by(name=name).one_or_none()
            if bpcostitem_name:
                return False, '❌ Такая статья затрат уже существует'
            # Если такой Компании не существует стандартное добавление
            bpcostitem = BusinessPlanCostItem(name=name,
                                  actual=True)
            db.add(bpcostitem)
            db.commit()
            return True, '✅ Статья затрат успешно добавлена!'
        except Exception as e:
            db.rollback()
            print(f'Ошибка добавления Статьи затрат: {e}')
            return False, '❌ Ошибка при добавлении Статьи затрат'
        finally:
            db.close()

    @staticmethod
    def db_bpcostitem_update(bpcostitem_id: int, name: str, note: str, actual: bool) -> tuple[bool, str]:
        """Обновление данных Статьи затрат в базе данных"""
        db = SessionLocal()
        try:
            # Особенность: для обновления данных, обновляемый объект должен быть получен
            # в рамках данной сессии. Если объект получить в другой сессии, а сюда
            # просто передать, то обновление данных в БД не произойдет!
            bpcostitem = db.query(BusinessPlanCostItem).filter_by(id=bpcostitem_id).one_or_none()
            # Предварительная проверка на существование Компании при обновлении наименования
            bpcostitem_name = db.query(BusinessPlanCostItem).filter_by(name=name).one_or_none()
            if bpcostitem_name:
                if bpcostitem_name.id == bpcostitem.id:
                    bpcostitem_name = None          
            if (bpcostitem_name != None):
                return False, '❌ Такая Статья затрат уже существует'
            # Если такой Компании не существует стандартное обновление            
            bpcostitem.name = name
            bpcostitem.note = note
            bpcostitem.actual = actual
            db.commit()
            return True, '✅ Данные по Статье затрат успешно обновлены!'
        except Exception as e:
            db.rollback()
            print(f'Ошибка обновления данных Статьи затрат: {e}')
            return False, '❌ Ошибка при обновлении данных Статьи затрат'
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