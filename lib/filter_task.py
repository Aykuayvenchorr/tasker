import sys
import os
# Абсолютный путь к родительской папке
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Добавляем родительскую папку в sys.path
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
from sqlalchemy.orm import Session

from models import (SessionLocal, Employee, Company, Division, License, Facility, Project, Permission)


def filter_task():
    db = SessionLocal()
    try:
        cur_emp = st.session_state.employee
        cur_emp_formatted = f'{cur_emp.id} {cur_emp.surname} {cur_emp.name[0].upper()}.'

        company = db.query(Company).filter_by(id=cur_emp.company).one_or_none()

        if company.name == 'ГПН-ГЕО':
            all_emps = db.query(Employee).all()
        else:
            all_emps = db.query(Employee).filter_by(company=company.id).all()
        options_employees = []
        for i in all_emps:
           options_employees.append(f'{i.id} {i.surname} {i.name[0].upper()}.') 
        employees = st.multiselect(label='Сотрудники',
                                   options=options_employees,
                                   default=cur_emp_formatted
                                  )
        emp = []
        for e in employees:
            emp.append(e.split()[0])

        permission = (
            db.query(Permission)
                .filter(
                    Permission.employee == cur_emp.id
                    )
                .first()
            )
        company_ids = [c.id for c in permission.companies]
        division_ids = [c.id for c in permission.divisions]
        companies_objs = []
        for c in company_ids:
            comp = db.query(Company).filter_by(id=c).one_or_none()
            companies_objs.append(comp)

        divisions_objs = []
        for c in division_ids:
            div = db.query(Division).filter_by(id=c).one_or_none()
            divisions_objs.append(div)

        companies = st.multiselect(label='Компании',
                                   options=companies_objs,
                                   format_func=lambda company: f'{company.name}')
        cmp = []
        for c in companies:
            cmp.append(c.id)
        divisions = st.multiselect(label='Подразделения',
                                   options=divisions_objs,
                                   format_func=lambda division: f'{division.name} ({division.abbr}) / {division.company_back.name}')
        dvs = []
        for d in divisions:
            dvs.append(d.id)
        licenses = st.multiselect(label='Лицензии',
                                   options=db.query(License).all())
        lics = []
        for l in licenses:
            lics.append(l.id)
    
        projects = st.multiselect(label='Проекты',
                                   options=db.query(Project).all())
        prjs = []
        for p in projects:
            prjs.append(p.id)
    
        facilities = st.multiselect(label='Объекты',
                                   options=db.query(Facility).all(),
                                   format_func=lambda facility: f'{facility.name} ({facility.license_back.name})')
        fcs =[]
        for f in facilities:
            fcs.append(f.id)
    
        result = {
            'employees': emp if emp else None,
            'companies': cmp if cmp else None,
            'divisions': dvs if dvs else None,
            'licenses': lics if lics else None,
            'projects': prjs if prjs else None,
            'facilities': fcs if fcs else None
        }
    except Exception as e:
        print(f'Ошибка получения filter_task: {e}')
    finally:
        db.close()
    return result