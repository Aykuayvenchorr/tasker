from typing import List
import pandas as pd
from models import SessionLocal, License, Company, Project


class ServiceLicense():
    """Сервис работы с лицензиями"""

    @staticmethod
    def get_licenses__companies(selected_companies, licenses_selected):
        """Список актуальных лицензий выделеных Компаний"""
        db = SessionLocal()
        companies_list_id = [company.id for company in selected_companies]
        licenses_selected_new = []
        try:
            lienses = db.query(License).filter(License.actual==True)
            lienses = lienses.filter(License.company.in_(companies_list_id)).all()
            if len(licenses_selected) > 0:
                for lic in lienses:
                    for lic_s in licenses_selected:
                        if lic_s == lic.id:
                            licenses_selected_new.append(lic)
                return licenses_selected_new, lienses
            else:
                return [], lienses
        except Exception as e:
            print(f'Ошибка получения списка лицензий: {e}')
            return [], []
        finally:
            db.close()


    @staticmethod
    def get_dataframe(switch_actual, company_name=None):
        db = SessionLocal()
        if company_name:
            company = db.query(Company).filter_by(name=company_name).one_or_none()

        try:
            if switch_actual:
                if company_name:
                    licenses = db.query(License).filter_by(actual=switch_actual, company_back=company).all()
                else:
                    licenses = db.query(License).filter_by(actual=switch_actual).all()
            else:
                if company_name:
                    licenses = db.query(License).filter_by(company_back=company).all()
                else:
                    licenses = db.query(License).all()
            
            licenses_data = [
                {'ID': c.id,
                 'name': c.name,
                 'dt_start': c.dt_start,
                 'dt_end': c.dt_end,
                 'company': c.company_back.name,
                 'actual': c.actual
                }
                for c in licenses]
            data_frame = pd.DataFrame(licenses_data)
            return True, data_frame
        except Exception as e:
            print(f'Ошибка получения лицензий: {e}')
            return False, None
        finally:
            db.close()

    @staticmethod
    def get_licenses(licenses_selected):
        """Список актуальных Лицензий"""
        db = SessionLocal()
        licenses_selected_new = []
        try:
            licenses = db.query(License).filter_by(actual=True).all()
            if len(licenses_selected) > 0:
                for lic in licenses:
                    for lic_s in licenses_selected:
                        if lic_s == lic.id:
                            licenses_selected_new.append(lic)
                return licenses_selected_new, licenses
            else:
                return [], licenses
        except Exception as e:
            print(f'Ошибка получения списка лицензий: {e}')
            return [], []
        finally:
            db.close()

    @staticmethod
    def get_license__id(id: int) -> License:
        """Получение Лицензий по его ID"""
        db = SessionLocal()
        try:
            return db.query(License).filter_by(id=id).one_or_none()
        except Exception as e:
            print(f'Ошибка получения лицензии по ID: {e}')
            return None
        finally:
            db.close()

    @staticmethod
    def get_license_names(company_name=None) -> List[str] | None:
        """Список имен актуальных Лицензий"""
        db = SessionLocal()
        try:
            if company_name:
                comp = db.query(Company).filter_by(name=company_name).one_or_none()
                licenses = db.query(License).filter_by(actual=True, company=comp.id).all()
            else:
                licenses = db.query(License).filter_by(actual=True).all()
        except Exception as e:
            print(f'Ошибка получения имен актуальных Лицензий: {e}')
        finally:
            db.close()

        # Преобразую данные в плоский список
        license_names = [license.name for license in licenses]
        # Добавляю пустой вариант для возможности пустого выбора
        license_names.insert(0, '')
        return license_names

    @staticmethod
    def db_license_insert(name: str, dt_start: str, dt_end: int, doc: str, note: str, company_name) -> tuple[bool, str]:
        """Добавление новой Лицензии в базу данных"""
        db = SessionLocal()
        try:
            # Предварительная проверка на существование заводимой Лицензии
            lic_name = db.query(License).filter_by(name=name).one_or_none()
            if lic_name:
                return False, '❌ Такая Лицензия уже существует'
            # Если такой Лицензии не существует стандартное добавление
            comp = db.query(Company).filter_by(name=company_name).one_or_none()

            lic = License(name=name,
                          dt_start=dt_start,
                          dt_end=dt_end,
                          doc=doc,
                          note=note,
                          company=comp.id,
                          actual=True)
            db.add(lic)
            db.commit()
            return True, '✅ Лицензия успешно добавлена!'
        except Exception as e:
            db.rollback()
            print(f'Ошибка добавления Лицензии: {e}')
            return False, '❌ Ошибка при добавлении Лицензии'
        finally:
            db.close()

    @staticmethod
    def db_license_update(license_id: int, name: str, dt_start: str, dt_end: int, doc: str, note: str, actual: bool, company_name) -> tuple[bool, str]:
        """Обновление даных Лицензии в базе данных"""
        db = SessionLocal()
        try:
            # Особенность: для обновления данных, обновляемый объект должен быть получен
            # в рамках данной сессии. Если объект получить в другой сессии, а сюда
            # просто передать, то обновление данных в БД не произойдет!
            license = db.query(License).filter_by(id=license_id).one_or_none()
            # Предварительная проверка на существование Подразделения при обновлении наименования
            lic_name = db.query(License).filter_by(name=name).one_or_none()
            
            if lic_name:
                if lic_name.id == license.id:
                    lic_name = None
                    
            if lic_name != None:
                return False, '❌ Такая Лицензия уже существует'
            # Если такой Лицензии не существует стандартное обновление
            company = db.query(Company).filter_by(name=company_name).one_or_none()
            license.name = name
            license.dt_start = dt_start
            license.dt_end = dt_end
            license.doc = doc
            license.note = note
            license.actual = actual
            license.company = company.id
            db.commit()
            return True, '✅ Данные по Лицензии успешно обновлены!'
        except Exception as e:
            db.rollback()
            print(f'Ошибка обновления данных Лицензии: {e}')
            return False, '❌ Ошибка при обновлении данных Лицензии'
        finally:
            db.close()

    @staticmethod
    def get_licenses__names(licenses_names):
        """Получение списка лицензий по их именам"""
        db = SessionLocal()
        try:
            return db.query(License).filter(License.name.in_(licenses_names)).all()
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения списка лицензий по их именам: {e}')
            return []
        finally:
            db.close()

    @staticmethod
    def get_licenses_names_by_project_id(project_id: int):
        """Получение списка лицензий по ID проекта"""
        db = SessionLocal()
        try:
            licenses = db.query(License).filter(License.projects.any(Project.id.in_([project_id]))).all()
            # licenses = db.query(License).filter(License.projects.id==project_id).all()
            current_licenses = [l.name for l in licenses]
            return current_licenses
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения списка лицензий по их именам: {e}')
            return []
        finally:
            db.close()
        