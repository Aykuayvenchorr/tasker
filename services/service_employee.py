from typing import List
import pandas as pd
from models import SessionLocal, Company, Employee, Division


class ServiceEmployee():
    """Сервис работы с сотрудниками"""

    @staticmethod
    def get_dataframe(switch_actual):
        db = SessionLocal()
        try:
            if switch_actual:
                employees = db.query(Employee).filter_by(actual=switch_actual).order_by(Employee.surname).all()
            else:
                employees = db.query(Employee).order_by(Employee.surname).all()
            employees_data = [
                {'ID': c.id,
                 'name': c.name,
                 'surname': c.surname,
                 'patronymic': c.patronymic,
                 'company': db.query(Company).filter_by(id=c.company).one_or_none().name,
                 'division': db.query(Division).filter_by(id=c.division).one_or_none().name,
                 'post': c.post,
                 'actual': c.actual
                }
                for c in employees]
            data_frame = pd.DataFrame(employees_data)
            return True, data_frame
        except Exception as e:
            print(f'Ошибка получения сотрудников: {e}')
            return False, None
        finally:
            db.close()

    @staticmethod
    def get_employees(employees_selected):
        """Список актуальных сотрудников"""
        db = SessionLocal()
        employees_selected_new = []
        try:
            employees = db.query(Employee).filter_by(actual=True).all()
            if len(employees_selected) > 0:
                for emp in employees:
                    for emp_s in employees_selected:
                        if emp_s == emp.id:
                            employees_selected_new.append(emp)
                return employees_selected_new, employees
            else:
                return [], employees
        except Exception as e:
            print(f'Ошибка получения списка сотрудников: {e}')
            return [], []
        finally:
            db.close()

    @staticmethod
    def get_employee__id(id: int) -> Employee:
        """Получение Сотрудника по его ID"""
        db = SessionLocal()
        try:
            return db.query(Employee).filter_by(id=id).one_or_none()
        except Exception as e:
            print(f'Ошибка получения Сотрудника по ID: {e}')
            return None
        finally:
            db.close()

    @staticmethod
    def get_employee_names() -> List[str] | None:
        """Список имен актуальных сотрудников"""
        db = SessionLocal()
        try:
            employees = db.query(Employee).filter_by(actual=True).all()
        except Exception as e:
            print(f'Ошибка получения имен актуальных сотрудников: {e}')
        finally:
            db.close()

        # Преобразую данные в плоский список
        employee_names = [employee.name for employee in employees]
        # Добавляю пустой вариант для возможности пустого выбора
        employee_names.insert(0, '')
        return employee_names

    @staticmethod
    def db_employee_insert(name: str, surname: str, patronymic: str, post: str, isdirector: bool, isadmin: bool, login: str, password: str, phone: str, email: str, date_birth, contacts: str, company, division, note: str) -> tuple[bool, str]:
        """Добавление нового Сотрудника в базу данных"""
        db = SessionLocal()
        try:
            # Предварительная проверка на существование заводимого Сотрудника
            emp_name = db.query(Employee).filter_by(name=name, surname=surname, patronymic=patronymic).one_or_none()
            if emp_name:
                return False, '❌ Такой Сотрудник  уже существует'
            # Если такого Сотрудника не существует стандартное добавление
            company_id = db.query(Company).filter_by(name=company).one_or_none().id
            division_id = db.query(Division).filter_by(company=company_id, name=division).one_or_none().id
            emp = Employee(name=name,
                           surname=surname,
                           patronymic=patronymic,
                           post=post,
                           isdirector=isdirector,
                           isadmin=isadmin,
                           login=login,
                           password=password,
                           phone=phone,
                           email=email,
                           date_birth=date_birth,
                           contacts=contacts,
                           company=company_id,
                           division=division_id,
                           note=note,
                           actual=True)
            db.add(emp)
            db.commit()
            return True, '✅ Сотрудник успешно добавлен!'
        except Exception as e:
            db.rollback()
            print(f'Ошибка добавления Сотрудника: {e}')
            return False, '❌ Ошибка при добавлении Сотрудника'
        finally:
            db.close()

    @staticmethod
    def db_employee_update(employee_id: int, name: str, surname: str, patronymic: str, post: str, isdirector: bool, isadmin: bool, login: str, password: str, phone: str, email: str, date_birth, contacts: str, company, division, note: str, actual: bool) -> tuple[bool, str]:
        """Обновление даных Компании в базе данных"""
        db = SessionLocal()
        try:
            # Особенность: для обновления данных, обновляемый объект должен быть получен
            # в рамках данной сессии. Если объект получить в другой сессии, а сюда
            # просто передать, то обновление данных в БД не произойдет!
            employee = db.query(Employee).filter_by(id=employee_id).one_or_none()
            # Предварительная проверка на существование Компании при обновлении наименования
            emp_name = db.query(Employee).filter_by(name=name, surname=surname, patronymic=patronymic).one_or_none()
            if emp_name:
                if emp_name.id == employee.id:
                    emp_name = None           
                if emp_name != None:
                    return False, '❌ Такой Сотрудник уже существует'
           
            # Если такого Сотрудника не существует стандартное обновление   

            company = db.query(Company).filter_by(name=company).one_or_none()
            division = db.query(Division).filter_by(company=company.id, name=division).one_or_none()
            employee.name = name
            employee.surname = surname
            employee.patronymic = patronymic
            employee.contacts = contacts
            employee.post = post
            employee.isdirector = isdirector
            employee.isadmin = isadmin
            employee.login = login
            employee.password = password
            employee.phone = phone
            employee.email = email
            employee.date_birth = date_birth
            employee.contacts = contacts
            employee.company = company.id
            employee.division = division.id
            employee.note = note
            employee.actual = actual
            db.commit()
            return True, '✅ Данные по Сотруднику успешно обновлены!'
        except Exception as e:
            db.rollback()
            print(f'Ошибка обновления данных Сотрудника: {e}')
            return False, '❌ Ошибка при обновлении данных Сотрудника'
        finally:
            db.close()

    @staticmethod
    def get_employees__names(employees_names):
        """Получение списка сотрудников по их именам"""
        db = SessionLocal()
        try:
            return  db.query(Employee).filter(Employee.name.in_(employees_names)).all()
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения списка сотрудников по их именам: {e}')
            return []
        finally:
            db.close()