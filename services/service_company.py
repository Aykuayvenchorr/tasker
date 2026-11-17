from typing import List
import pandas as pd
from models import SessionLocal, Company


class ServiceCompany():
    """Сервис работы с компаниями"""

    @staticmethod
    def get_dataframe(switch_actual):
        db = SessionLocal()
        try:
            if switch_actual:
                companies = db.query(Company).filter_by(actual=switch_actual).all()
            else:
                companies = db.query(Company).all()
            companies_data = [
                {'ID': c.id,
                 'name': c.name,
                 'full_name': c.full_name,
                 'parent': (f"({c.parent}) {db.query(Company).filter_by(id=c.parent).one_or_none().company_dict()['full_name']}" if c.parent else None),
                 'actual': c.actual
                }
                for c in companies]
            data_frame = pd.DataFrame(companies_data)
            return True, data_frame
        except Exception as e:
            print(f'Ошибка получения компаний: {e}')
            return False, None
        finally:
            db.close()

    @staticmethod
    def get_companies(companies_selected):
        """Список актуальных Компаний"""
        db = SessionLocal()
        companies_selected_new = []
        try:
            companies = db.query(Company).filter_by(actual=True).all()
            if len(companies_selected) > 0:
                for cmp in companies:
                    for cmp_s in companies_selected:
                        if cmp_s == cmp.id:
                            companies_selected_new.append(cmp)
                return companies_selected_new, companies
            else:
                return [], companies
        except Exception as e:
            print(f'Ошибка получения списка Компаний: {e}')
            return [], []
        finally:
            db.close()

    @staticmethod
    def get_company__id(id: int) -> Company:
        """Получение Компании по ее ID"""
        db = SessionLocal()
        try:
            return db.query(Company).filter_by(id=id).one_or_none()
        except Exception as e:
            print(f'Ошибка получения компании по ID: {e}')
            return None
        finally:
            db.close()

    @staticmethod
    def get_company_names() -> List[str] | None:
        """Список имен актуальных компаний"""
        db = SessionLocal()
        try:
            companies = db.query(Company).filter_by(actual=True).all()
        except Exception as e:
            print(f'Ошибка получения компании по ID: {e}')
        finally:
            db.close()

        # Преобразую данные в плоский список
        company_names = [company.name for company in companies]
        # Добавляю пустой вариант для возможности пустого выбора
        company_names.insert(0, '')
        return company_names

    @staticmethod
    def db_company_insert(name: str, full_name: str, parent: int, note: str) -> tuple[bool, str]:
        """Добавление новой Компании в базу данных"""
        db = SessionLocal()
        try:
            # Предварительная проверка на существование заводимой Компании
            cmp_name = db.query(Company).filter_by(name=name).one_or_none()
            cmp_fname = db.query(Company).filter_by(full_name=full_name).one_or_none()
            if cmp_name or cmp_fname:
                return False, '❌ Такая Компания уже существует'
            # Если такой Компании не существует стандартное добавление
            cmp = Company(name=name,
                          full_name=full_name,
                          note=note,
                          actual=True)
            db.add(cmp)
            db.commit()
            if parent:
                cmpp = db.query(Company).filter_by(name=parent).one_or_none()
                cmp.parent = cmpp.id
                db.commit()
            return True, '✅ Компания успешно добавлена!'
        except Exception as e:
            db.rollback()
            print(f'Ошибка добавления Компании: {e}')
            return False, '❌ Ошибка при добавлении Компании'
        finally:
            db.close()

    @staticmethod
    def db_company_update(company_id: int, name: str, full_name: str, parent: int, contacts: str, note: str, actual: bool, logo: str) -> tuple[bool, str]:
        """Обновление даных Компании в базе данных"""
        db = SessionLocal()
        try:
            # Особенность: для обновления данных, обновляемый объект должен быть получен
            # в рамках данной сессии. Если объект получить в другой сессии, а сюда
            # просто передать, то обновление данных в БД не произойдет!
            company = db.query(Company).filter_by(id=company_id).one_or_none()
            # Предварительная проверка на существование Компании при обновлении наименования
            cmp_name = db.query(Company).filter_by(name=name).one_or_none()
            cmp_fname = db.query(Company).filter_by(full_name=full_name).one_or_none()
            if cmp_name.id == company.id:
                cmp_name = None
            if cmp_fname.id == company.id:
                cmp_fname = None            
            if (cmp_name != None) or (cmp_fname != None):
                return False, '❌ Такая Компания уже существует'
            # Если такой Компании не существует стандартное обновление            
            company.name = name
            company.full_name = full_name            
            if parent:
                company_parent = db.query(Company).filter_by(name=parent).one_or_none()
                company.parent = company_parent.id
            else:
                company.parent = None
            company.logo = logo
            company.contacts = contacts
            company.note = note
            company.actual = actual
            db.commit()
            return True, '✅ Данные по Компании успешно обновлены!'
        except Exception as e:
            db.rollback()
            print(f'Ошибка обновления данных Компании: {e}')
            return False, '❌ Ошибка при обновлении данных Компании'
        finally:
            db.close()

    @staticmethod
    def get_companies__names(companies_names):
        """Получение списка компаний по их именам"""
        db = SessionLocal()
        try:
            return  db.query(Company).filter(Company.name.in_(companies_names)).all()
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения списка компаний по их именам: {e}')
            return []
        finally:
            db.close()