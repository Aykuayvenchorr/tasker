import os
import uuid
import psycopg2
import enum
from dotenv import load_dotenv
from typing import Optional
from datetime import datetime, date

from sqlalchemy import create_engine, MetaData, ForeignKey, text, Column, Table, Index, func, UniqueConstraint, Integer, String, Text, Boolean, Date, DateTime, Float, Enum
from sqlalchemy.orm import DeclarativeBase, sessionmaker, mapped_column, Mapped, relationship


############################################
#
#   Настройка окружения
#
############################################

load_dotenv(override=True)

USER = os.environ.get('USER')
PASSWORD = os.environ.get('PASSWORD')
HOST = 'spb99akl-pg01'
# DB_NAME = 'datalake'
DB_NAME = 'bdgeo'
PORT = 5432
"""
Если в пароле имеются спецсимволы: @, :, /, # то парсер считает его разделителем для host и всему трындец...
Для решения данной проблемы необходимо закодировать пароль в URL-формате (URL-encoding)
@ -> %40
: -> %3A
/ -> %2F
# -> %23
"""


############################################
#
#   Подключение к PostgreSQL
#
############################################
"<dialect>+<driver>://<username>:<password>@<host>:<port>/<database>"
postgresql_db_url = f'postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}'
postgresql_db_url = f'postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}'
# engine = create_engine(postgresql_db_url, echo=True, future=True)
engine = create_engine(postgresql_db_url, future=True)
SessionLocal = sessionmaker(bind=engine)


############################################
#
#   Базовая модель
#
############################################
class Base(DeclarativeBase):
    metadata = MetaData(schema="geo_umzr")
    note: Mapped[Optional[str]] = mapped_column(String, nullable=True, doc="Примечание")
    actual: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", doc="Актуальность")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), doc="Создан")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), doc="Обновлен")
    gis: Mapped[Optional[str]] = mapped_column(String, nullable=True, doc="GIS ID")
    gist: Mapped[Optional[str]] = mapped_column(String, nullable=True, doc="GIS таблица")


############################################
#
#   Связующие таблицы для many-to-many
#
############################################
# Таблица связи mamy-to-many (License - Project)
association_table_license_project = Table(
    'association_license_project',
    Base.metadata,
    Column('id_license', Integer, ForeignKey('geo_umzr.licenses.id'), primary_key=True),
    Column('id_project', Integer, ForeignKey('geo_umzr.projects.id'), primary_key=True)
)

# Таблица связи mamy-to-many (Task - Company)
association_table_task_company = Table(
    'association_task_company',
    Base.metadata,
    Column('id_task', Integer, ForeignKey('geo_umzr.tasks.id'), primary_key=True),
    Column('id_company', Integer, ForeignKey('geo_umzr.companies.id'), primary_key=True)
)

# Таблица связи mamy-to-many (Task - Division)
association_table_task_division = Table(
    'association_task_division',
    Base.metadata,
    Column('id_task', Integer, ForeignKey('geo_umzr.tasks.id'), primary_key=True),
    Column('id_division', Integer, ForeignKey('geo_umzr.divisions.id'), primary_key=True)
)

# Таблица связи mamy-to-many (Task - License)
association_table_task_license = Table(
    'association_task_license',
    Base.metadata,
    Column('id_task', Integer, ForeignKey('geo_umzr.tasks.id'), primary_key=True),
    Column('id_license', Integer, ForeignKey('geo_umzr.licenses.id'), primary_key=True)
)

# Таблица связи mamy-to-many (Task - Project)
association_table_task_project = Table(
    'association_task_project',
    Base.metadata,
    Column('id_task', Integer, ForeignKey('geo_umzr.tasks.id'), primary_key=True),
    Column('id_project', Integer, ForeignKey('geo_umzr.projects.id'), primary_key=True)
)

# Таблица связи mamy-to-many (Task - Facility)
association_table_task_facility = Table(
    'association_task_facility',
    Base.metadata,
    Column('id_task', Integer, ForeignKey('geo_umzr.tasks.id'), primary_key=True),
    Column('id_facility', Integer, ForeignKey('geo_umzr.facility.id'), primary_key=True)
)

# Таблица связи mamy-to-many (Permission - Company)
association_table_permission_company = Table(
    'association_permission_company',
    Base.metadata,
    Column('id_permission', Integer, ForeignKey('geo_umzr.permissions.id'), primary_key=True),
    Column('id_company', Integer, ForeignKey('geo_umzr.companies.id'), primary_key=True)
)

# Таблица связи mamy-to-many (Permission - Division)
association_table_permission_division = Table(
    'association_permission_division',
    Base.metadata,
    Column('id_permission', Integer, ForeignKey('geo_umzr.permissions.id'), primary_key=True),
    Column('id_division', Integer, ForeignKey('geo_umzr.divisions.id'), primary_key=True)
)
############################################
#
#   Модели таблиц структуры
#
############################################
class Company(Base):
    __tablename__ = "companies"
    __table_args__ = {'schema': 'geo_umzr', 'comment': 'Компании'}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, doc="Краткое наименование")
    full_name: Mapped[str] = mapped_column(String, doc="Полное наименование")    
    parent: Mapped[int | None] = mapped_column(ForeignKey("geo_umzr.companies.id", ondelete="SET NULL"), nullable=True, doc="Головная компания")
    children: Mapped[list['Company']] = relationship('Company', back_populates='parent_back', passive_deletes=True, single_parent=True)
    parent_back: Mapped[Optional['Company']] = relationship('Company', back_populates='children', remote_side='Company.id')
    logo: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    contacts: Mapped[Optional[str]] = mapped_column(Text, nullable=True, doc='Контакты')
    employee_back: Mapped[list['Employee']] = relationship('Employee', back_populates='company_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь
    division_back: Mapped[list['Division']] = relationship('Division', back_populates='company_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь
    license_back: Mapped[list['License']] = relationship('License', back_populates='company_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь
    bpstr_back: Mapped[list['BusinessPlanStr']] = relationship('BusinessPlanStr', back_populates='company_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь
    tasks: Mapped[list['Task']] = relationship('Task', secondary=association_table_task_company, back_populates='companies')
    permissions: Mapped[list['Permission']] = relationship('Permission', secondary=association_table_permission_company, back_populates='companies')

    # task_back: Mapped[list['Task']] = relationship('Task', back_populates='company_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь
    comment_back: Mapped[list['Comment']] = relationship('Comment', back_populates='company_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь

    def __str__(self):
        return f"{self.name} ({self.full_name})"

    def __repr__(self):
        return f"{self.name}"

    def company_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'full_name': self.full_name,
            'parent': self.parent,
            'logo': self.logo,
            'contacts': self.contacts
        }

    def get_name(self):
        return f"{self.id}_{self.name}"


class Division(Base):
    __tablename__ = "divisions"
    __table_args__ = (UniqueConstraint("name", "company", name="uniq_division"), {'schema': 'geo_umzr', 'comment': 'Подразделения'})
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, doc="Наименование")
    abbr: Mapped[str] = mapped_column(String, doc="Аббревиатура")
    parent: Mapped[int | None] = mapped_column(ForeignKey("geo_umzr.divisions.id", ondelete="SET NULL"), nullable=True, doc="Руководящее подразделение")
    children: Mapped[list["Division"]] = relationship("Division", back_populates="parent_back", passive_deletes=True, single_parent=True)
    parent_back: Mapped[Optional["Division"]] = relationship("Division", back_populates="children", remote_side=[id])
    contacts: Mapped[Optional[str]] = mapped_column(Text, nullable=True, doc="Контакты")
    company: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.companies.id', ondelete='CASCADE'), nullable=False)
    company_back: Mapped["Company"] = relationship('Company', back_populates='division_back')   # Обратная связь
    employee_back: Mapped[list['Employee']] = relationship('Employee', back_populates='division_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь
    project_back: Mapped[list['Project']] = relationship('Project', back_populates='division_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь
    # task_back: Mapped[list['Task']] = relationship('Task', back_populates='division_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь
    tasks: Mapped[list['Task']] = relationship('Task', secondary=association_table_task_division, back_populates='divisions')
    comment_back: Mapped[list['Comment']] = relationship('Comment', back_populates='division_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь
    permissions: Mapped[list['Permission']] = relationship('Permission', secondary=association_table_permission_division, back_populates='divisions')

    # def __str__(self):
    #     return f"{self.name} ({self.abbr}) / {self.company_back} / {self.parent_back}"

    def __repr__(self):
        return f"{self.name} ({self.abbr}) / {self.company_back} / {self.parent_back}"

    def division_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'abbr': self.abbr,
            'parent': self.parent,
            'contacts': self.contacts,
            'company': self.company
        }

    def get_name(self):
        return f"{self.id}_{self.company_back.name}_{self.abbr}"

class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (UniqueConstraint("name", "surname", "post", "company", "division", name="uniq_empoloyee"), {'schema': 'geo_umzr', 'comment': 'Сотрудники'})
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, doc="Имя")
    surname: Mapped[str] = mapped_column(String, doc="Фамилия")
    patronymic: Mapped[Optional[str]] = mapped_column(String, nullable=True, doc="Отчество")
    post: Mapped[str] = mapped_column(String, doc="Должность")
    isdirector: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", doc="Руководитель")
    login: Mapped[str] = mapped_column(String, doc="Логин")
    password: Mapped[str] = mapped_column(String, doc="Пароль")
    isadmin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", doc="Администратор")
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True, doc="Телефон")
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True, doc="Электронная почта")
    logo: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    date_birth: Mapped[Optional[date]] = mapped_column(Date, doc="Дата рождения")
    contacts: Mapped[Optional[str]] = mapped_column(Text, nullable=True, doc="Контакты")
    company: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.companies.id', ondelete='CASCADE'), nullable=False)
    company_back: Mapped['Company'] = relationship('Company', back_populates='employee_back')   # Обратная связь
    division: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.divisions.id', ondelete='CASCADE'), nullable=False)
    division_back: Mapped['Division'] = relationship('Division', back_populates="employee_back")   # Обратная связь
    task_created_back: Mapped[list['Task']] = relationship('Task', back_populates="employee_created_back", foreign_keys="Task.employee_created")   # Обратная связь
    task_responsible_back: Mapped[list['Task']] = relationship('Task', back_populates="employee_responsible_back", foreign_keys="Task.employee_responsible")   # Обратная связь
    task_ended_back: Mapped[list['Task']] = relationship('Task', back_populates="employee_ended_back", foreign_keys="Task.employee_ended")   # Обратная связь
    plandatestart_created_back: Mapped[list['PlanDateStart']] = relationship('PlanDateStart', back_populates="employee_created_back")   # Обратная связь
    plandateend_created_back: Mapped[list['PlanDateEnd']] = relationship('PlanDateEnd', back_populates="employee_created_back")   # Обратная связь
    comment_created_back: Mapped[list['Comment']] = relationship('Comment', back_populates='employee_created_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь
    permission_back: Mapped[list['Permission']] = relationship('Permission', back_populates='employee_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь

    # def __str__(self):
    #     return f"{self.id} {self.surname} {self.name} - {self.post} ({self.company_back.name} {self.division_back.name})"

    # def __repr__(self):
    #     return f"{self.id} {self.surname} {self.name} - {self.post} ({self.company_back.name} {self.division_back.name})"

    def employee_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'surname': self.surname,
            'patronymic': self.patronymic,
            'post': self.post,
            'isdirector': self.isdirector,
            'login': self.login,
            'password': self.password,
            'isadmin': self.isadmin,
            'phone': self.phone,
            'email': self.email,
            'logo': self.logo,
            'date_birth': self.date_birth,
            'contacts': self.contacts,
            'company': self.company,
            'division': self.division
        }


class License(Base):
    __tablename__ = "licenses"
    __table_args__ = (UniqueConstraint("name", "company", name="uniq_license"), {'schema': 'geo_umzr', 'comment': 'Лицензии'})
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, doc="Наименование")
    dt_start: Mapped[date] = mapped_column(Date, doc="Дата получения")
    dt_end: Mapped[date] = mapped_column(Date, doc="Дата окончания")
    doc: Mapped[Optional[str]] = mapped_column(String, nullable=True, doc="Местоположение")
    file: Mapped[Optional[str]] = mapped_column(String, nullable=True, doc="Файл")
    company: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.companies.id', ondelete='CASCADE'), nullable=False)
    company_back: Mapped['Company'] = relationship('Company', back_populates='license_back')   # Обратная связь
    facility_back: Mapped['Facility'] = relationship('Facility', back_populates='license_back')   # Обратная связь
    projects: Mapped[list['Project']] = relationship('Project', secondary=association_table_license_project, back_populates='licenses')
    # task_back: Mapped[list['Task']] = relationship('Task', back_populates='license_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь
    tasks: Mapped[list['Task']] = relationship('Task', secondary=association_table_task_license, back_populates='licenses')
    comment_back: Mapped[list['Comment']] = relationship('Comment', back_populates='license_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f"{self.name}"

    def license_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'dt_start': self.dt_start,
            'dt_end': self.dt_end,
            'doc': self.doc,
            'company': self.company
        }

    def get_name(self):
        return f"{self.id}_{self.name}"


class FacilityType(Base):
    __tablename__ = "facility_type"
    __table_args__ = {'schema': 'geo_umzr', 'comment': 'Тип объекта'}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, doc="Наименование")
    facility_back: Mapped[list['Facility']] = relationship('Facility', back_populates='ftype_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f"repr: {self.name}"

    def facility_type_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }


class Facility(Base):
    __tablename__ = "facility"
    __table_args__ = (UniqueConstraint('name', 'parent', 'license', name='uniq_facility'), {'schema': 'geo_umzr', 'comment': 'Объект'})
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, doc="Наименование")
    count: Mapped[Optional[float]] = mapped_column(Float, nullable=True, doc="Количество")
    length: Mapped[Optional[float]] = mapped_column(Float, nullable=True, doc="Протяженность")
    square: Mapped[Optional[float]] = mapped_column(Float, nullable=True, doc="Площадь")
    license: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.licenses.id', ondelete='CASCADE'), nullable=False)
    license_back: Mapped['License'] = relationship('License', back_populates='facility_back')   # Обратная связь    
    parent: Mapped[int | None] = mapped_column(ForeignKey("geo_umzr.facility.id", ondelete="SET NULL"), nullable=True, doc="Основной объект")
    children: Mapped[list['Facility']] = relationship('Facility', back_populates='parent_back', passive_deletes=True, single_parent=True)
    parent_back: Mapped[Optional['Facility']] = relationship('Facility', back_populates='children', remote_side='Facility.id')    
    ftype: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.facility_type.id', ondelete='CASCADE'), nullable=False)
    ftype_back: Mapped['FacilityType'] = relationship('FacilityType', back_populates='facility_back')   # Обратная связь
    # bpstr_back: Mapped["BusinessPlanStr"] = relationship('BusinessPlanStr', back_populates='facility_back')   # Обратная связь
    # task_back: Mapped[list['Task']] = relationship('Task', back_populates='facility_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь
    tasks: Mapped[list['Task']] = relationship('Task', secondary=association_table_task_facility, back_populates='facilities')
    comment_back: Mapped[list['Comment']] = relationship('Comment', back_populates='facility_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь

    def __str__(self):
        return f"{self.name} - {self.license}"

    def __repr__(self):
        return f"{self.name} - {self.license}"

    def facility_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'count': self.count,
            'length': self.length,
            'square': self.square,
            'license': self.license,
            'parent': self.parent,
            'ftype': self.ftype
        }

    def get_name(self):
        return f"{self.id}_{self.license_back.name}_{self.name}"


############################################
#
#   Модели таблиц экономики
#
############################################
class Project(Base):
    __tablename__ = "projects"
    __table_args__ = {'schema': 'geo_umzr', 'comment': 'Проекты'}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, doc="Наименование")
    contacts: Mapped[Optional[str]] = mapped_column(String, doc="Контакты")
    division: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.divisions.id', ondelete='CASCADE'), nullable=True)
    division_back: Mapped["Division"] = relationship('Division', back_populates='project_back')   # Обратная связь
    licenses: Mapped[list["License"]] = relationship("License", secondary=association_table_license_project, back_populates="projects")
    tasks: Mapped[list['Task']] = relationship('Task', secondary=association_table_task_facility, back_populates='facilities')

    businessplan_back: Mapped[list['BusinessPlan']] = relationship('BusinessPlan', back_populates='project_back')   # Обратная связь
    # businessplan_back: Mapped[list['BusinessPlan']] = relationship('BusinessPlan', secondary=association_table_bp_project, back_populates='projects')   # Обратная связь
    # task_back: Mapped[list['Task']] = relationship('Task', back_populates='project_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь
    tasks: Mapped[list['Task']] = relationship('Task', secondary=association_table_task_project, back_populates='projects')
    comment_back: Mapped[list['Comment']] = relationship('Comment', back_populates='project_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь

    bpfacility_back: Mapped["BusinessPlanFacility"] = relationship('BusinessPlanFacility', back_populates='project_back')   # Обратная связь

    
    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f"{self.name}"

    def project_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contacts': self.contacts,
            'division': self.division,
            'licenses': self.licenses
        }

    def get_name(self):
        return f"{self.id}_{self.division_back.company_back.name}_{self.division_back.abbr}_{self.name}"


class ProjectStage(Base):
    __tablename__ = "projectstage"
    __table_args__ = {'schema': 'geo_umzr', 'comment': 'Этапы проекта'}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, doc="Наименование")
    bpstr_back: Mapped[list["BusinessPlanStr"]] = relationship('BusinessPlanStr', back_populates='stage_back')   # Обратная связь

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f"repr: {self.name}"


class BusinessPlan(Base):
    __tablename__ = "businessplans"
    __table_args__ = {'schema': 'geo_umzr', 'comment': 'Бизнес планы'}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, doc="Наименование")
    date: Mapped[date] = mapped_column(Date, doc="Дата бизнес плана")
    project: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.projects.id', ondelete='CASCADE'), nullable=True)
    project_back: Mapped["Project"] = relationship('Project', back_populates='businessplan_back')   # Обратная связь
    bpstr_back: Mapped[list["BusinessPlanStr"]] = relationship('BusinessPlanStr', back_populates='businessplan_back')   # Обратная связь
    # projects: Mapped[list['Project']] = relationship('Project', secondary=association_table_bp_project, back_populates='businessplan_back')
    parent: Mapped[int | None] = mapped_column(ForeignKey("geo_umzr.businessplans.id", ondelete="SET NULL"), nullable=True, doc="Головной бизнес-план")
    children: Mapped[list['BusinessPlan']] = relationship('BusinessPlan', back_populates='parent_back', passive_deletes=True, single_parent=True)
    parent_back: Mapped[Optional['BusinessPlan']] = relationship('BusinessPlan', back_populates='children', remote_side='BusinessPlan.id')
    doc: Mapped[Optional[str]] = mapped_column(String, nullable=True, doc="Местоположение")
    
    def __str__(self):
        return f"{self.name} - {self.project}"

    def __repr__(self):
        return f"repr: {self.name} - {self.project}"

    def busplan_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'date': self.date,
            'project': self.project
        }

    # def get_name(self):
    #     return f"{self.id}_{self.project_back.name}_{self.name}"

        
class BusinessPlanCostItem(Base):
    """Статьи затрат (Аренда, ЗУР, Горный отвод...)"""
    __tablename__ = "businessplancostitems"
    __table_args__ = {'schema': 'geo_umzr', 'comment': 'Статьи затрат'}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, doc="Наименование")
    bpstr_back: Mapped[list["BusinessPlanStr"]] = relationship('BusinessPlanStr', back_populates='costitem_back')   # Обратная связь

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f"repr: {self.name}"


class BusinessPlanFacility(Base):
    """Объект в БП"""
    __tablename__ = "businessfacilities"
    __table_args__ = {'schema': 'geo_umzr', 'comment': 'Объект из Бизнес плана'}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, doc="Наименование")
    project: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.projects.id', ondelete='CASCADE'), nullable=True)
    project_back: Mapped["Project"] = relationship('Project', back_populates='bpfacility_back')   # Обратная связь
    count: Mapped[Optional[float]] = mapped_column(Float, nullable=True, doc="Количество")
    length: Mapped[Optional[float]] = mapped_column(Float, nullable=True, doc="Протяженность")
    square: Mapped[Optional[float]] = mapped_column(Float, nullable=True, doc="Площадь")
    bpstr_back: Mapped[list["BusinessPlanStr"]] = relationship('BusinessPlanStr', back_populates='bpfacility_back')   # Обратная связь

    def __str__(self):
        return f"{self.name} - {self.project}"

    def __repr__(self):
        return f"repr: {self.name} - {self.project}"


class BusinessPlanStr(Base):
    __tablename__ = "businessplanstr"
    __table_args__ = {'schema': 'geo_umzr', 'comment': 'Строка Бизнес плана'}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    businessplan: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.businessplans.id', ondelete='CASCADE'), nullable=True)
    businessplan_back: Mapped["BusinessPlan"] = relationship('BusinessPlan', back_populates='bpstr_back')   # Обратная связь    
    company: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.companies.id', ondelete='CASCADE'), nullable=True)
    company_back: Mapped["Company"] = relationship('Company', back_populates='bpstr_back')   # Обратная связь
    bpfacility: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.businessfacilities.id', ondelete='CASCADE'), nullable=True)
    bpfacility_back: Mapped["BusinessPlanFacility"] = relationship('BusinessPlanFacility', back_populates='bpstr_back')   # Обратная связь
    costitem: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.businessplancostitems.id', ondelete='CASCADE'), nullable=True)
    costitem_back: Mapped["BusinessPlanCostItem"] = relationship('BusinessPlanCostItem', back_populates='bpstr_back')   # Обратная связь
    stage: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.projectstage.id', ondelete='CASCADE'), nullable=True)
    stage_back: Mapped["ProjectStage"] = relationship('ProjectStage', back_populates='bpstr_back')   # Обратная связь
    # facility: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.facility.id', ondelete='CASCADE'), nullable=True)
    # facility_back: Mapped["Facility"] = relationship('Facility', back_populates='bpstr_back')   # Обратная связь
    # bptask_back: Mapped[list["BPTask"]] = relationship('BPTask', back_populates='bpstr_back')   # Обратная связь
    job_back: Mapped[list["Job"]] = relationship('Job', back_populates='bpstr_back')   # Обратная связь
    source_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('geo_umzr.businessplanstr.id', ondelete='CASCADE'), nullable=True)

    
class Job(Base):
    __tablename__ = "job"
    __table_args__ = {'schema': 'geo_umzr', 'comment': 'Сроки и оплата по бизнес-плану'}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dt_start: Mapped[date] = mapped_column(Date, doc="Плановая дата начала по бизнес-плану", nullable=True)
    dt_end: Mapped[date] = mapped_column(Date, doc="Плановая дата завершения по бизнес-плану", nullable=True)
    plan_fin_dt: Mapped[date] = mapped_column(Date, doc="Плановая дата финансирования по бизнес-плану", nullable=True)
    plan_fin_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True, doc="Плановая стоимость финансирования по бизнес-плану")
    plan_dev_dt: Mapped[date] = mapped_column(Date, doc="Плановая дата освоения по бизнес-плану", nullable=True)
    plan_dev_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True, doc="Плановая стоимость освоения по бизнес-плану")
    bpstr: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.businessplanstr.id', ondelete='CASCADE'), nullable=True)
    bpstr_back: Mapped["BusinessPlanStr"] = relationship('BusinessPlanStr', back_populates='job_back')   # Обратная связь
    task_back: Mapped[list["Task"]] = relationship('Task', back_populates='job_back')   # Обратная связь

    def __str__(self):
        return f"{self.id} - {self.bpstr_back.name}"

    def __repr__(self):
        return f"repr: {self.id} - {self.bpstr_back.name}"


# class BPTask(Base):
#     __tablename__ = "bptasks"
#     __table_args__ = {'schema': 'geo_umzr', 'comment': 'Производство (задача согласно БП)'}
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     name: Mapped[str] = mapped_column(String, doc="Наименование")
#     bpstr: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.businessplanstr.id', ondelete='CASCADE'), nullable=True)
#     bpstr_back: Mapped["BusinessPlanStr"] = relationship('BusinessPlanStr', back_populates='bptask_back')   # Обратная связь
#     dpb: Mapped[date] = mapped_column(Date, doc="Плановая дата начала")
#     dpe: Mapped[date] = mapped_column(Date, doc="Плановая дата окончания")
#     paymentbptask_back: Mapped[list["PaymentBPTask"]] = relationship('PaymentBPTask', back_populates='bptask_back')   # Обратная связь

#     def __str__(self):
#         return f"{self.name}"

#     def __repr__(self):
#         return f"repr: {self.name}"


# class PaymentBPTask(Base):
#     __tablename__ = "paymentbptask"
#     __table_args__ = {'schema': 'geo_umzr', 'comment': 'Оплата планируемая согласно Бизнес плана'}
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     bptask: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.bptasks.id', ondelete='CASCADE'), nullable=True, doc="Задача по бизнес плану")
#     bptask_back: Mapped["BPTask"] = relationship('BPTask', back_populates='paymentbptask_back')   # Обратная связь
#     date_develop: Mapped[date] = mapped_column(Date, doc="Дата освоения")
#     date_funding: Mapped[date] = mapped_column(Date, doc="Дата финансирования")
#     costp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, doc="Плановая стоимость")
#     task: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('geo_umzr.tasks.id', ondelete='CASCADE'), nullable=True, doc="Задача")
#     task_back: Mapped["Task"] = relationship('Task', back_populates='paymentBpTask')   # Обратная связь


############################################
#
#   Модели таблиц задач
#
############################################
class TaskStatusEnum(enum.Enum):
    __table_args__ = {'schema': 'geo_umzr', 'comment': 'Статусы задач'}

    NOT_STARTED = 'Не начата'
    WORKED = 'В работе'
    CANCELED = 'Отменена'
    ENDED = 'Завершена'


class TaskImportanceEnum(enum.Enum):
    __table_args__ = {'schema': 'geo_umzr', 'comment': 'Важности задач'}

    LOW = 'Низкая'
    MIDDLE = 'Средняя'
    HIGH = 'Высокая'


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = {'schema': 'geo_umzr', 'comment': 'Задачи'}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, doc="Наименование")
    desc: Mapped[str] = mapped_column(Text, nullable=True, doc="Описание")
    parent: Mapped[int | None] = mapped_column(ForeignKey("geo_umzr.tasks.id", ondelete="SET NULL"), nullable=True, doc="Головная задача")
    children: Mapped[list['Task']] = relationship('Task', back_populates='parent_back', passive_deletes=True, single_parent=True)
    parent_back: Mapped[Optional['Task']] = relationship('Task', back_populates='children', remote_side='Task.id')
    employee_created: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.employees.id', ondelete='CASCADE'), nullable=True, doc="Создатель")
    employee_created_back: Mapped["Employee"] = relationship('Employee', back_populates='task_created_back', foreign_keys=[employee_created])   # Обратная связь
    employee_responsible: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.employees.id', ondelete='CASCADE'), nullable=True, doc="Ответственный")
    employee_responsible_back: Mapped["Employee"] = relationship('Employee', back_populates='task_responsible_back', foreign_keys=[employee_responsible])   # Обратная связь
    employee_ended: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.employees.id', ondelete='CASCADE'), nullable=True, doc="Завершивший")
    employee_ended_back: Mapped["Employee"] = relationship('Employee', back_populates='task_ended_back', foreign_keys=[employee_ended])   # Обратная связь (Когда несколько полей на одну и ту же табл, foreignkey указывается напрямую
    dt_ended: Mapped[date] = mapped_column(Date, nullable=True, doc="Дата завершения")
    companies: Mapped[list['Company']] = relationship('Company', secondary=association_table_task_company, back_populates='tasks')
    divisions: Mapped[list['Division']] = relationship('Division', secondary=association_table_task_division, back_populates='tasks')
    licenses: Mapped[list['License']] = relationship('License', secondary=association_table_task_license, back_populates='tasks')
    projects: Mapped[list['Project']] = relationship('Project', secondary=association_table_task_project, back_populates='tasks')
    facilities: Mapped[list['Facility']] = relationship('Facility', secondary=association_table_task_facility, back_populates='tasks')

    # company: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.companyes.id', ondelete='CASCADE'), nullable=True)
    # company_back: Mapped['Company'] = relationship('Company', back_populates='task_back')   # Обратная связь
    # division: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.divisions.id', ondelete='CASCADE'), nullable=True)
    # division_back: Mapped['Division'] = relationship('Division', back_populates='task_back')   # Обратная связь
    # project: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.projects.id', ondelete='CASCADE'), nullable=True)
    # project_back: Mapped['Project'] = relationship('Project', back_populates='task_back')   # Обратная связь
    # license: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.licenses.id', ondelete='CASCADE'), nullable=True)
    # license_back: Mapped['License'] = relationship('License', back_populates='task_back')   # Обратная связь
    # facility: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.facility.id', ondelete='CASCADE'), nullable=True)
    # facility_back: Mapped['Facility'] = relationship('Facility', back_populates='task_back')   # Обратная связь
    
    fact_fin_dt: Mapped[date] = mapped_column(Date, doc="Фактическая дата оплаты", nullable=True)
    fact_fin_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True, doc="Фактическая стоимость")
    fact_dev_dt: Mapped[date] = mapped_column(Date, doc="Дата освоения", nullable=True)
    fact_dev_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True, doc="Стоимость освоения")
    cost_info: Mapped[str] = mapped_column(Text, nullable=True, doc="Примечание по оплате")
    status: Mapped['TaskStatusEnum'] = mapped_column(Enum(TaskStatusEnum, name='taskstatusenum'), default=TaskStatusEnum.NOT_STARTED, doc="Статус задачи", nullable=False)
    importance: Mapped['TaskImportanceEnum'] = mapped_column(Enum(TaskImportanceEnum, name='taskimportanceenum'), default=TaskImportanceEnum.MIDDLE, doc="Важность задачи", nullable=False)
    doc: Mapped[Optional[str]] = mapped_column(String, nullable=True, doc="Местоположение")
    plandatestart_back: Mapped[list['PlanDateStart']] = relationship('PlanDateStart', back_populates='task_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь
    plandateend_back: Mapped[list['PlanDateEnd']] = relationship('PlanDateEnd', back_populates='task_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь
    plancost_back: Mapped[list['PlanCost']] = relationship('PlanCost', back_populates='task_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь
    comment_back: Mapped[list['Comment']] = relationship('Comment', back_populates='task_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь
    # paymentBpTask: Mapped[list['PaymentBPTask']] = relationship('PaymentBPTask', back_populates='task_back', cascade='all, delete-orphan', passive_deletes=True)   # Обратная связь

    job: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.job.id', ondelete='CASCADE'), nullable=True)
    job_back: Mapped["Job"] = relationship('Job', back_populates='task_back')   # Обратная связь
    actual_bp: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", doc="Актуальность")


    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f"repr: {self.name}"

    def task_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'desc': self.desc,
            'parent': self.parent,
            'children': self.children,
            'employee_created': self.employee_created,
            'employee_responsible': self.employee_responsible,
            'employee_ended': self.employee_ended,
            'dt_ended': self.dt_ended,
            'company': self.companies,
            'division': self.divisions,
            'project': self.projects,
            'license': self.licenses,
            'facility': self.facilities,
            'fact_fin_dt': self.fact_fin_dt,
            'fact_fin_cost': self.fact_fin_cost,
            'fact_dev_dt': self.fact_dev_dt,
            'fact_dev_cost': self.fact_dev_cost,
            'cost_info': self.cost_info,
            'status': self.status,
            'importance': self.importance,
            'doc': self.doc,
            'actual': self.actual
        }


class PlanDateStart(Base):
    __tablename__ = "plandatestart"
    __table_args__ = {'schema': 'geo_umzr', 'comment': 'Плановая дата начала задачи'}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.tasks.id', ondelete='CASCADE'), nullable=True)
    task_back: Mapped['Task'] = relationship('Task', back_populates='plandatestart_back')   # Обратная связь
    dt_start: Mapped[date] = mapped_column(Date, doc="Плановая дата начала", nullable=True)
    employee_created: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.employees.id', ondelete='CASCADE'), nullable=True, doc="Создатель")
    employee_created_back: Mapped["Employee"] = relationship('Employee', back_populates='plandatestart_created_back')   # Обратная связь


class PlanDateEnd(Base):
    __tablename__ = "plandateend"
    __table_args__ = {'schema': 'geo_umzr', 'comment': 'Плановая дата завершения задачи'}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.tasks.id', ondelete='CASCADE'), nullable=True)
    task_back: Mapped['Task'] = relationship('Task', back_populates='plandateend_back')   # Обратная связь
    dt_end: Mapped[date] = mapped_column(Date, doc="Плановая дата завершения", nullable=True)
    employee_created: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.employees.id', ondelete='CASCADE'), nullable=True, doc="Создатель")
    employee_created_back: Mapped["Employee"] = relationship('Employee', back_populates='plandateend_created_back')   # Обратная связь


class PlanCost(Base):
    __tablename__ = "plancost"
    __table_args__ = {'schema': 'geo_umzr', 'comment': 'Плановая оплата'}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.tasks.id', ondelete='CASCADE'), nullable=True)
    task_back: Mapped['Task'] = relationship('Task', back_populates='plancost_back')   # Обратная связь
    plan_fin_dt: Mapped[date] = mapped_column(Date, doc="Плановая дата оплаты", nullable=True)
    plan_fin_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True, doc="Плановая стоимость финансирования")
    plan_dev_dt: Mapped[date] = mapped_column(Date, doc="Плановая дата освоения", nullable=True)
    plan_dev_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True, doc="Плановая стоимость освоения")
    nds: Mapped[int] = mapped_column(Integer,  nullable=True)
    ndfl: Mapped[int] = mapped_column(Integer,  nullable=True)
    
    def __str__(self):
        return f"{self.task}"

    def __repr__(self):
        return f"repr: {self.task} {self.plan_fin_dt} {self.plan_fin_cost} {self.plan_dev_dt} {self.plan_dev_cost}  {self.actual}"

############################################
#
#   Модель таблицы комментариев
#
############################################

class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = {'schema': 'geo_umzr', 'comment': 'Комментарии'}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, doc="Краткие сведения")
    full_name: Mapped[str] = mapped_column(Text, nullable=True, doc="Полный комментарий")
    parent: Mapped[int | None] = mapped_column(ForeignKey("geo_umzr.comments.id", ondelete="SET NULL"), nullable=True, doc="Головной комментарий")
    children: Mapped[list['Comment']] = relationship('Comment', back_populates='parent_back', passive_deletes=True, single_parent=True)
    parent_back: Mapped[Optional['Comment']] = relationship('Comment', back_populates='children', remote_side='Comment.id')
    employee_created: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.employees.id', ondelete='CASCADE'), nullable=True, doc="Создатель")
    employee_created_back: Mapped["Employee"] = relationship('Employee', back_populates='comment_created_back')   # Обратная связь
    company: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.companies.id', ondelete='CASCADE'), nullable=True)
    company_back: Mapped['Company'] = relationship('Company', back_populates='comment_back')   # Обратная связь
    division: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.divisions.id', ondelete='CASCADE'), nullable=True)
    division_back: Mapped['Division'] = relationship('Division', back_populates='comment_back')   # Обратная связь
    project: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.projects.id', ondelete='CASCADE'), nullable=True)
    project_back: Mapped['Project'] = relationship('Project', back_populates='comment_back')   # Обратная связь
    license: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.licenses.id', ondelete='CASCADE'), nullable=True)
    license_back: Mapped['License'] = relationship('License', back_populates='comment_back')   # Обратная связь
    facility: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.facility.id', ondelete='CASCADE'), nullable=True)
    facility_back: Mapped['Facility'] = relationship('Facility', back_populates='comment_back')   # Обратная связь
    task: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.tasks.id', ondelete='CASCADE'), nullable=True)
    task_back: Mapped['Task'] = relationship('Task', back_populates='comment_back')   # Обратная связь
    doc: Mapped[Optional[str]] = mapped_column(String, nullable=True, doc="Местоположение")

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f"repr: {self.name}"

class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = {'schema': 'geo_umzr', 'comment': 'Доступы'}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee: Mapped[int] = mapped_column(Integer, ForeignKey('geo_umzr.employees.id', ondelete='CASCADE'), nullable=True, doc="Сотрудник")
    employee_back: Mapped["Employee"] = relationship('Employee', back_populates='permission_back')   # Обратная связь
    companies: Mapped[list['Company']] = relationship('Company', secondary=association_table_permission_company, back_populates='permissions')
    divisions: Mapped[list['Division']] = relationship('Division', secondary=association_table_permission_division, back_populates='permissions')


if __name__ == "__main__":
    # Base.metadata.drop_all(engine)
    # Base.metadata.create_all(engine)
    Base.metadata.create_all(bind=engine, tables=[Job.__table__])