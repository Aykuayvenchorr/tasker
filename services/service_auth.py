from models import SessionLocal, Employee


class ServiceAuth():
    """Сервис работы с пользователем"""

    @staticmethod
    def get_empoyee(user):
        db = SessionLocal()
        try:
            employee = db.query(Employee).filter_by(note=user).one_or_none()
            return employee if employee else None
        except Exception as e:
            print(f'Ошибка получения сотрудника: {e}')
        finally:
            db.close()


    @staticmethod
    def get_employee__id(pk: int) -> Employee:
        db = SessionLocal()
        try:
            employee = db.query(Employee).filter_by(id=pk).one_or_none()
            return employee if employee else None
        except Exception as e:
            print(f'Ошибка получения сотрудника по ID: {e}')
        finally:
            db.close()

    @staticmethod
    def get_admin(user):
        db = SessionLocal()
        try:
            employee = db.query(Employee).filter_by(note=user).one_or_none()
            admin = employee.isadmin
            return admin
        except Exception as e:
            print(f'Ошибка получения admin: {e}')
        finally:
            db.close()