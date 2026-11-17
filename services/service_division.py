from typing import List
import pandas as pd
from utils.helpers import Helpers
from models import SessionLocal, Company, Division
from collections import defaultdict

class ServiceDivision():
    """Сервис работы с подразделениями"""

    @staticmethod
    def get_divisions__companies(selected_companies, divisions_selected):
        """Список актуальных подразделений выделеных Компаний"""
        db = SessionLocal()
        companies_list_id = [company.id for company in selected_companies]
        divisions_selected_new = []
        try:
            # Словарь Компаний
            companies = db.query(Company).filter(Company.actual==True).all()
            companies_dict = {}
            for company in companies:
                companies_dict[company.id] = company.name
            # Подразделения выбранных Компаний
            divisions = db.query(Division).filter(Division.actual==True)
            divisions = divisions.filter(Division.company.in_(companies_list_id))
            divisions = divisions.order_by(Division.company, Division.name).all()
            # divisions = divisions.filter(Division.parent==None).order_by(Division.company, Division.name).all()

            # Обновляем перечень выбранных подразделений в текущей сессии
            if len(divisions_selected) > 0:
                for division in divisions:
                    for division_s in divisions_selected:
                        if division_s == division.id:
                            divisions_selected_new.append(division)
            divisions_selected_id = [division.id for division in divisions_selected_new]
            str_ierarchy = []
            str_selected = []
            return Helpers.ierarchy(divisions, divisions_selected_id, companies_dict, str_ierarchy, str_selected, 0, 'company')
        except Exception as e:
            print(f'Ошибка получения списка подразделений: {e}')
            return [], []
        finally:
            db.close()

    @staticmethod
    def walk_tree(tree, result, parent=None):
        for div in tree[parent]:
            result.append(div)
            ServiceDivision.walk_tree(
                tree,
                result,
                div.id
            )

    @staticmethod
    def get_dataframe(switch_actual, company_name=None):
        db = SessionLocal()
        if company_name:
            company = db.query(Company).filter_by(name=company_name).one_or_none()

        try:
            if switch_actual:
                if company_name:
                    divisions = db.query(Division).filter_by(actual=switch_actual, company_back=company).all()
                else:
                    divisions = db.query(Division).filter_by(actual=switch_actual).all()
            else:
                if company_name:
                    divisions = db.query(Division).filter_by(company_back=company).all()
                else:
                    divisions = db.query(Division).all()

            tree = defaultdict(list)
            for div in divisions:
                tree[div.parent].append(div)
            for children in tree.values():
                children.sort(key=lambda x: x.name.lower())
            result = []
            ServiceDivision.walk_tree(tree, result)

            divisions = result
            
            divisions_data = [
                {'ID': c.id,
                 'name': c.name,
                 'abbr': c.abbr,
                 'parent': (f"({c.parent}) {db.query(Division).filter_by(id=c.parent).one_or_none().division_dict()['name']}" if c.parent else None),
                 'company': c.company_back.name,
                 'actual': c.actual
                }
                for c in divisions]
            data_frame = pd.DataFrame(divisions_data)
            return True, data_frame
        except Exception as e:
            print(f'Ошибка получения подразделений: {e}')
            return False, None
        finally:
            db.close()

    @staticmethod
    def get_divisions(divisions_selected):
        """Список актуальных Подразделений"""
        db = SessionLocal()
        divisions_selected_new = []
        try:
            divisions = db.query(Division).filter_by(actual=True).all()
            if len(divisions_selected) > 0:
                for div in divisions:
                    for div_s in divisions_selected:
                        if div_s == div.id:
                            divisions_selected_new.append(div)
                return divisions_selected_new, divisions
            else:
                return [], divisions
        except Exception as e:
            print(f'Ошибка получения списка Подразделений: {e}')
            return [], []
        finally:
            db.close()

    @staticmethod
    def get_division__id(id: int) -> Division:
        """Получение Подразделения по его ID"""
        db = SessionLocal()
        try:
            return db.query(Division).filter_by(id=id).one_or_none()
        except Exception as e:
            print(f'Ошибка получения подразделения по ID: {e}')
            return None
        finally:
            db.close()

    @staticmethod
    def get_division_names(company_name=None) -> List[str] | None:
        """Список имен актуальных Подразделений"""
        db = SessionLocal()
        try:
            if company_name:
                comp = db.query(Company).filter_by(name=company_name).one_or_none()
                divisions = db.query(Division).filter_by(actual=True, company=comp.id).all()
            else:
                divisions = db.query(Division).filter_by(actual=True).all()
        except Exception as e:
            print(f'Ошибка получения подразделения по ID: {e}')
        finally:
            db.close()

        # Преобразую данные в плоский список
        division_names = [division.name for division in divisions]
        # Добавляю пустой вариант для возможности пустого выбора
        division_names.insert(0, '')
        return division_names

    @staticmethod
    def db_division_insert(name: str, abbr: str, parent: int, note: str, company_name) -> tuple[bool, str]:
        """Добавление нового Подразделения в базу данных"""
        db = SessionLocal()
        try:
            # Предварительная проверка на существование заводимого Подразделения
            div_name = db.query(Division).filter_by(name=name).one_or_none()
            div_abbr = db.query(Division).filter_by(abbr=abbr).one_or_none()
            if div_name or div_abbr:
                return False, '❌ Такое Подразделение уже существует'
            # Если такого Подразделения не существует стандартное добавление
            comp = db.query(Company).filter_by(name=company_name).one_or_none()

            div = Division(name=name,
                          abbr=abbr,
                          note=note,
                          company=comp.id,
                          actual=True)
            db.add(div)
            db.commit()
            if parent:
                divp = db.query(Division).filter_by(name=parent).one_or_none()
                div.parent = divp.id
                db.commit()
            return True, '✅ Подразделение успешно добавлена!'
        except Exception as e:
            db.rollback()
            print(f'Ошибка добавления Подразделения: {e}')
            return False, '❌ Ошибка при добавлении Подразделения'
        finally:
            db.close()

    @staticmethod
    def db_division_update(division_id: int, name: str, abbr: str, parent: int, contacts: str, note: str, actual: bool, company_name) -> tuple[bool, str]:
        """Обновление даных Подразделения в базе данных"""
        db = SessionLocal()
        try:
            # Особенность: для обновления данных, обновляемый объект должен быть получен
            # в рамках данной сессии. Если объект получить в другой сессии, а сюда
            # просто передать, то обновление данных в БД не произойдет!
            division = db.query(Division).filter_by(id=division_id).one_or_none()
            # Предварительная проверка на существование Подразделения при обновлении наименования
            div_name = db.query(Division).filter_by(name=name).one_or_none()
            div_abbr = db.query(Division).filter_by(abbr=abbr).one_or_none()
            if div_name:
                if div_name.id == division.id:
                    div_name = None
            if div_abbr:
                if div_abbr.id == division.id:
                    div_abbr = None
            if (div_name != None) or (div_abbr != None):
                return False, '❌ Такое Подразделение уже существует'
            # Если такого Подразделения не существует стандартное обновление            
            division.name = name
            division.abbr = abbr
            company = db.query(Company).filter_by(name=company_name).one_or_none()
            if parent:
                division_parent = db.query(Division).filter_by(name=parent, company=company.id).one_or_none()
                division.parent = division_parent.id
            else:
                division.parent = None
            division.contacts = contacts
            division.note = note
            division.actual = actual
            division.company = company.id
            db.commit()
            return True, '✅ Данные по Подразделению успешно обновлены!'
        except Exception as e:
            db.rollback()
            print(f'Ошибка обновления данных Подразделения: {e}')
            return False, '❌ Ошибка при обновлении данных Подразделения'
        finally:
            db.close()

    @staticmethod
    def get_divisions__names(divisions_names):
        """Получение списка подразделения по их именам"""
        db = SessionLocal()
        try:
            return  db.query(Division).filter(Division.name.in_(divisions_names)).all()
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения списка подразделений по их именам: {e}')
            return []
        finally:
            db.close()

    @staticmethod
    def get_division_company_name(division):
        """Получение имени компании у подразделения"""
        db = SessionLocal()
        try:
            division_cmp_id = db.query(Division).filter_by(id=division.id).one_or_none().company
            comp_name = db.query(Company).filter_by(id=division_cmp_id).one_or_none().name
            return comp_name
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения имени компании у подразделения: {e}')
            return []
        finally:
            db.close()
        