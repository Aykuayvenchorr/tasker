from typing import List
import pandas as pd
from utils.helpers import Helpers
from models import SessionLocal, License, Facility, FacilityType


class ServiceFacility():
    """Сервис работы с объектами"""

    @staticmethod
    def get_facilities__licenses(selected_licenses, facilities_selected):
        """Список актуальных объектов выделеных лицензий"""
        db = SessionLocal()
        licenses_list_id = [license.id for license in selected_licenses]
        facilities_selected_new = []
        try:
            # Словарь лицензий
            licenses = db.query(License).filter(License.actual==True).all()
            licenses_dict = {}
            for license in licenses:
                licenses_dict[license.id] = license.name
            # Объекты выбранных лицензий
            facilities = db.query(Facility).filter(Facility.actual==True)
            facilities = facilities.filter(Facility.license.in_(licenses_list_id))
            facilities = facilities.filter(Facility.parent==None).order_by(Facility.license, Facility.name).all()
            # Обновляем перечень выбранных объектов в текущей сессии
            if len(facilities_selected) > 0:
                for facility in facilities:
                    for facility_s in facilities_selected:
                        if facility_s == facility.id:
                            facilities_selected_new.append(facility)

            facilities_selected_id = [facility.id for facility in facilities_selected_new]
            str_ierarchy = []
            str_selected = []
            return Helpers.ierarchy(facilities, facilities_selected_id, licenses_dict, str_ierarchy, str_selected, 0, 'license')
        except Exception as e:
            print(f'Ошибка получения списка объектов: {e}')
            return [], []
        finally:
            db.close()

    @staticmethod
    def get_dataframe(switch_actual, license_name=None):
        db = SessionLocal()
        if license_name:
            license = db.query(License).filter_by(name=license_name).one_or_none()

        try:
            if switch_actual:
                if license_name:
                    facilities = db.query(Facility).filter_by(actual=switch_actual, license_back=license).all()
                else:
                    facilities = db.query(Facility).filter_by(actual=switch_actual).all()
            else:
                if license_name:
                    facilities = db.query(Facility).filter_by(license_back=license).all()
                else:
                    facilities = db.query(Facility).all()
            
            facilities_data = [
                {'ID': c.id,
                 'name': c.name,
                 'ftype': db.query(FacilityType).filter_by(id=c.ftype).one_or_none().name,
                 'parent': db.query(Facility).filter_by(id=c.parent).one_or_none().name if c.parent else None,
                 'license': db.query(License).filter_by(id=c.license).one_or_none().name,
                 'actual': c.actual
                }
                for c in facilities]
            data_frame = pd.DataFrame(facilities_data)
            return True, data_frame
        except Exception as e:
            print(f'Ошибка получения объектов: {e}')
            return False, None
        finally:
            db.close()

    @staticmethod
    def get_facilities(facilities_selected):
        """Список актуальных объектов"""
        db = SessionLocal()
        facilities_selected_new = []
        try:
            facilities = db.query(Facility).filter_by(actual=True).all()
            if len(facilities_selected) > 0:
                for fc in facilities:
                    for fc_s in facilities_selected:
                        if fc_s == fc.id:
                            facilities_selected_new.append(fc)
                return facilities_selected_new, facilities
            else:
                return [], facilities
        except Exception as e:
            print(f'Ошибка получения списка объектов: {e}')
            return [], []
        finally:
            db.close()

    @staticmethod
    def get_facility__id(id: int) -> Facility:
        """Получение Объекта по его ID"""
        db = SessionLocal()
        try:
            return db.query(Facility).filter_by(id=id).one_or_none()
        except Exception as e:
            print(f'Ошибка получения объекта по ID: {e}')
            return None
        finally:
            db.close()

    @staticmethod
    def get_facility_names(license_name=None) -> List[str] | None:
        """Список имен актуальных Объектов"""
        db = SessionLocal()
        try:
            if license_name:
                license = db.query(License).filter_by(name=license_name).one_or_none()
                facilities = db.query(Facility).filter_by(actual=True, license=license.id).all()
            else:
                facilities = db.query(Facility).filter_by(actual=True).all()
        except Exception as e:
            print(f'Ошибка получения объектов по имени лицензии: {e}')
        finally:
            db.close()

        # Преобразую данные в плоский список
        facility_names = [facility.name for facility in facilities]
        # Добавляю пустой вариант для возможности пустого выбора
        facility_names.insert(0, '')
        return facility_names

    @staticmethod
    def db_facility_insert(name: str, count: float, length: float, square: float, license_name, ftype_name, note: str, parent=None) -> tuple[bool, str]:
        """Добавление нового Объекта в базу данных"""
        db = SessionLocal()
        try:
            lic = db.query(License).filter_by(name=license_name).one_or_none()
            # Предварительная проверка на существование заводимого Объекта
            fc_name = db.query(Facility).filter_by(name=name, license=lic.id).one_or_none()
            if fc_name:
                return False, '❌ Такой Объект уже существует'
            # Если такого Объекта не существует стандартное добавление
            
            ftype = db.query(FacilityType).filter_by(name=ftype_name).one_or_none()

            facility = Facility(name=name,
                                count=count,
                                length=length,
                                square=square,
                                license=lic.id,
                                ftype=ftype.id,
                                note=note)
            db.add(facility)
            db.commit()
            if parent:
                facility_p = db.query(Facility).filter_by(name=parent).one_or_none()
                facility.parent = facility_p.id
                db.commit()
            return True, '✅ Объект успешно добавлен!'
        except Exception as e:
            db.rollback()
            print(f'Ошибка добавления Объекта: {e}')
            return False, '❌ Ошибка при добавлении Объекта'
        finally:
            db.close()

    @staticmethod
    def db_facility_update(facility_id: int, name: str, count: float, length: float, square: float, license_name, ftype_name, note: str, actual: bool, parent=None) -> tuple[bool, str]:
        """Обновление даных Объекта в базе данных"""
        db = SessionLocal()
        try:
            # Особенность: для обновления данных, обновляемый объект должен быть получен
            # в рамках данной сессии. Если объект получить в другой сессии, а сюда
            # просто передать, то обновление данных в БД не произойдет!
            facility = db.query(Facility).filter_by(id=facility_id).one_or_none()
            # Предварительная проверка на существование Объекта при обновлении наименования
            lic = db.query(License).filter_by(name=license_name).one_or_none()
            ftype = db.query(FacilityType).filter_by(name=ftype_name).one_or_none()
            facility_name = db.query(Facility).filter_by(name=name, license=lic.id, ftype=ftype.id).one_or_none()
            
            if facility_name:
                if facility_name.id == facility.id:
                    facility_name = None
                    
            if facility_name != None:
                return False, '❌ Такой Объект уже существует'
            # Если такого Объекта не существует стандартное обновление
            facility.name = name
            facility.count = count
            facility.length = length
            facility.square = square
            facility.license = lic.id
            facility.ftype = ftype.id
            facility.note = note
            facility.actual = actual
            if parent:
                facility_parent = db.query(Facility).filter_by(name=parent, license=lic.id).one_or_none()
                facility.parent = facility_parent.id
            else:
                facility.parent = None
            db.commit()
            return True, '✅ Данные по Объекту успешно обновлены!'
        except Exception as e:
            db.rollback()
            print(f'Ошибка обновления данных Объекта: {e}')
            return False, '❌ Ошибка при обновлении данных Объекта'
        finally:
            db.close()

    @staticmethod
    def get_facilities__names(facilities_names):
        """Получение списка объектов по их именам"""
        db = SessionLocal()
        try:
            return db.query(Facility).filter(Facility.name.in_(facilities_names)).all()
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения списка объектов по их именам: {e}')
            return []
        finally:
            db.close()

    @staticmethod
    def get_ftype_names():
        """Получение списка имен типов объекта"""
        db = SessionLocal()
        try:
            ftypes = db.query(FacilityType).all()
            ftype_names = [f.name for f in ftypes]
            return ftype_names
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения списка имен типов объекта: {e}')
            return []
        finally:
            db.close()

    @staticmethod
    def get_ftype__id(id: int) -> FacilityType:
        """Получение Типа Объекта по его ID"""
        db = SessionLocal()
        try:
            return db.query(FacilityType).filter_by(id=id).one_or_none()
        except Exception as e:
            print(f'Ошибка получения типа объекта по ID: {e}')
            return None
        finally:
            db.close()

    @staticmethod
    def db_ftype_insert(ftype_name: str) -> FacilityType:
        """Добавление нового Типа Объекта в базу данных"""
        db = SessionLocal()
        try:
            # Предварительная проверка на существование заводимого Типа Объекта
            ft_name = db.query(FacilityType).filter_by(name=ftype_name).one_or_none()
            if ft_name:
                return False, '❌ Такой Тип Объекта уже существует'
            # Если такого Типа Объекта не существует стандартное добавление
            ftype = FacilityType(name=ftype_name)
            db.add(ftype)
            db.commit()
            return True, '✅ Тип объекта успешно добавлен!'
        except Exception as e:
            db.rollback()
            print(f'Ошибка добавления Типа Объекта: {e}')
            return False, '❌ Ошибка при добавлении Типа Объекта'
        finally:
            db.close()