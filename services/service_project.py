from typing import List
import pandas as pd
from sqlalchemy import and_, or_
from models import SessionLocal, License, Division, Project, Company, BusinessPlan


class ServiceProject():
    """Сервис работы с проектами"""

    @staticmethod
    def get_projects__licenses_divisions(selected_licenses, selected_divisions, projects_selected):
        """Список актуальных проектов"""
        db = SessionLocal()
        selected_licenses_id = [license.id for license in selected_licenses]
        selected_divisions_id = [division[0] for division in selected_divisions]
        projects_selected_new = []
        try:
            projects = db.query(Project).filter(
                and_(
                    Project.actual == True,
                    or_(
                        Project.division.in_(selected_divisions_id),
                        Project.licenses.any(License.id.in_(selected_licenses_id))
                    )
                )
            ).order_by(Project.name).all()
            # Обновляем перечень выбранных проектов в текущей сессии
            if len(projects_selected) > 0:
                for project in projects:
                    for project_s in projects_selected:
                        if project_s == project.id:
                            projects_selected_new.append(project)
                return projects_selected_new, projects
            else:
                return [], projects
        except Exception as e:
            print(f'Ошибка получения списка проектов: {e}')
            return [], []
        finally:
            db.close()


    @staticmethod
    def get_dataframe(switch_actual, division_name=None, company_name=None):
        db = SessionLocal()
        try:
            if division_name != '' and company_name != '':
                company = db.query(Company).filter_by(name=company_name).one_or_none()
                division = db.query(Division).filter_by(name=division_name, company_back=company).one_or_none()
                if switch_actual:
                    projects = db.query(Project).filter_by(actual=switch_actual, division_back=division).all()
                else:
                    projects = db.query(Project).filter_by(division_back=division).all()

            elif division_name == '' and company_name != '':
                company = db.query(Company).filter_by(name=company_name).one_or_none()
                divisions = db.query(Division).filter(Division.company==company.id).all()
                divisions = [div.id for div in divisions]
                if switch_actual:
                    projects = db.query(Project).filter(Project.actual==switch_actual, Project.division.in_(divisions)).all()
                else:
                    projects = db.query(Project).filter(Project.division.in_(divisions)).all()
            elif division_name != '' and company_name == '':
                division = db.query(Division).filter_by(name=division_name).one_or_none().id
                if switch_actual:
                    projects = db.query(Project).filter(Project.actual==switch_actual, Project.division==division).all()
                else:
                    projects = db.query(Project).filter(Project.division==division).all()
                    
            else:
                projects = []

            projects_data = [
                    {'ID': c.id,
                     'name': c.name,
                     'division': db.query(Division).filter_by(id=c.division).one_or_none().name,
                     'licenses': ', '.join([l.name for l in c.licenses]),
                     'actual': c.actual
                    }
                    for c in projects]
            data_frame = pd.DataFrame(projects_data)
            return True, data_frame
        except Exception as e:
            print(f'Ошибка получения проектов: {e}')
            return False, None
        finally:
            db.close()

    @staticmethod
    def get_projects(projects_selected):
        """Список актуальных Проектов"""
        db = SessionLocal()
        projects_selected_new = []
        try:
            projects = db.query(Project).filter_by(actual=True).all()
            if len(projects_selected) > 0:
                for proj in projects:
                    for proj_s in projects_selected:
                        if proj_s == proj.id:
                            projects_selected_new.append(proj)
                return projects_selected_new, projects
            else:
                return [], projects
        except Exception as e:
            print(f'Ошибка получения списка проектов: {e}')
            return [], []
        finally:
            db.close()

    @staticmethod
    def get_project__id(id: int) -> Project:
        """Получение Проектов по его ID"""
        db = SessionLocal()
        try:
            return db.query(Project).filter_by(id=id).one_or_none()
        except Exception as e:
            print(f'Ошибка получения проекта по ID: {e}')
            return None
        finally:
            db.close()

    @staticmethod
    def get_project_names(division_name=None) -> List[str] | None:
        """Список имен актуальных Проектов"""
        db = SessionLocal()
        try:
            if division_name:
                div = db.query(Division).filter_by(name=division_name).one_or_none()
                projects = db.query(Project).filter_by(actual=True, division=div.id).all()
            else:
                projects = db.query(Project).filter_by(actual=True).all()
        except Exception as e:
            print(f'Ошибка получения проектов по ID: {e}')
        finally:
            db.close()

        # Преобразую данные в плоский список
        project_names = [project.name for project in projects]
        # Добавляю пустой вариант для возможности пустого выбора
        project_names.insert(0, '')
        return project_names

    @staticmethod
    def db_project_insert(name: str, contacts: str, note: str, company_name, division_name, licenses) -> tuple[bool, str]:
        """Добавление нового Проекта в базу данных"""
        db = SessionLocal()
        try:
            # Предварительная проверка на существование заводимоого проекта
            proj_name = db.query(Project).filter_by(name=name).one_or_none()
            if proj_name:
                return False, '❌ Такой Проект уже существует'
            # Если такого Проекта не существует стандартное добавление
            cmp = db.query(Company).filter_by(name=company_name).one_or_none()
            div = db.query(Division).filter_by(name=division_name, company=cmp.id).one_or_none()

            project = Project(name=name,
                           contacts=contacts,
                           note=note,
                           division=div.id,
                           actual=True)
            db.add(project)
            db.commit()
            if licenses != '':
                for lname in licenses:
                    license = db.query(License).filter_by(name=lname).one_or_none()
                    if license:
                        project.licenses.append(license)
            db.commit()
            return True, '✅ Проект успешно добавлен!'
        except Exception as e:
            db.rollback()
            print(f'Ошибка добавления Проекта: {e}')
            return False, '❌ Ошибка при добавлении Проекта'
        finally:
            db.close()

    @staticmethod
    def db_project_update(project_id: int, name: str, contacts: str, note: str, actual: bool, company_name, division, licenses) -> tuple[bool, str]:
        """Обновление даных Проекта в базе данных"""
        db = SessionLocal()
        try:
            # Особенность: для обновления данных, обновляемый объект должен быть получен
            # в рамках данной сессии. Если объект получить в другой сессии, а сюда
            # просто передать, то обновление данных в БД не произойдет!
            project = db.query(Project).filter_by(id=project_id).one_or_none()
            # Предварительная проверка на существование Проекта при обновлении наименования
            proj_name = db.query(Project).filter_by(name=name).one_or_none()
            
            if proj_name:
                if proj_name.id == project.id:
                    proj_name = None
                    
            if proj_name != None:
                return False, '❌ Такой Проект уже существует'
            # Если такого Проекта не существует стандартное обновление            
            project.name = name
            project.note = note
            project.actual = actual
            cmp = db.query(Company).filter_by(name=company_name).one_or_none()
            division_id = db.query(Division).filter_by(name=division, company=cmp.id).one_or_none().id
            project.division = division_id
            project.licenses.clear()
            for lname in licenses:
                license = db.query(License).filter_by(name=lname).one_or_none()
                if license:
                    project.licenses.append(license)
            db.commit()
            return True, '✅ Данные по Проекту успешно обновлены!'
        except Exception as e:
            db.rollback()
            print(f'Ошибка обновления данных Проекта: {e}')
            return False, '❌ Ошибка при обновлении данных Проекта'
        finally:
            db.close()

    @staticmethod
    def get_projects__names(projects_names):
        """Получение списка проектов по их именам"""
        db = SessionLocal()
        try:
            return  db.query(Project).filter(Project.name.in_(projects_names)).all()
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения списка проектов по их именам: {e}')
            return []
        finally:
            db.close()


    @staticmethod
    def get_project_name(project_id):
        """Получение имени проекта по id"""
        db = SessionLocal()
        try:
            return db.query(Project).filter_by(id=project_id).one_or_none().name
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения имени проекта по ID: {e}')
            return []
        finally:
            db.close()

    @staticmethod
    def get_project_names_by_busplan_id(busplan_id: int):
        """Получение списка проектов по ID Бизнес-плана"""
        db = SessionLocal()
        try:
            projects = db.query(Project).filter(Project.businessplan_back.any(BusinessPlan.id.in_([busplan_id]))).all()
            # licenses = db.query(License).filter(License.projects.id==project_id).all()
            current_projects = [l.name for l in projects]
            return current_projects
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения списка проектов по их именам: {e}')
            return []
        finally:
            db.close()

    @staticmethod
    def get_project_by_busplan_id(busplan_id: int):
        """Получение проекта по id busplan_id"""
        db = SessionLocal()
        try:
            busplan = db.query(BusinessPlan).filter_by(id=busplan_id).one_or_none()
            return db.query(Project).filter_by(id=busplan.project).one_or_none()
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения проекта по ID busplan_id: {e}')
            return []
        finally:
            db.close()

    @staticmethod
    def get_project_license_companies(project_id: int):
        """Получение компаний по лицензиям проекта"""
        db = SessionLocal()
        try:
            project = db.query(Project).filter_by(id=project_id).one_or_none()
            # Лицензии, связанные с проектом
            licenses = project.licenses
            # Компании, которым принадлежат эти лицензии
            company_ids = list({
                license.company
                for license in licenses
                if license.company is not None
            })
            return company_ids
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения компаний по лицензиям проекта: {e}')
            return []
        finally:
            db.close()

    @staticmethod
    def get_project_licenses(project_id: int):
        """Получение лицензий проекта"""
        db = SessionLocal()
        try:
            project = db.query(Project).filter_by(id=project_id).one_or_none()
            # Лицензии, связанные с проектом
            licenses = project.licenses
            license_ids = [license.id for license in licenses]
            return license_ids
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения лицензий проекта: {e}')
            return []
        finally:
            db.close()