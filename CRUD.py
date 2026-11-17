from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import delete, text
# from models import engine, Company, Division, Employee, License, Project, Task, TaskImportanceEnum, TaskStatusEnum, Facility, FacilityType, association_table_license_project, BusinessPlanCostItem, ProjectStage, BusinessPlanStr, BusinessPlanFacility, BusinessPlan, Comment association_table_task_company, PlanCost, PlanDateEnd, PlanDateStart
from models import engine, Task

if __name__ == "__main__":
    # with Session(engine) as session:
        with engine.begin() as conn:

        #     # BusinessPlanStr
            conn.execute(text("""
                ALTER TABLE geo_umzr.businessplanstr
                ADD COLUMN source_id INTEGER
                REFERENCES geo_umzr.businessplanstr(id)
                ON DELETE CASCADE;
            """))

        #     # Task
        #     conn.execute(text("""
        #         ALTER TABLE geo_umzr.tasks
        #             ADD COLUMN IF NOT EXISTS bpstr INTEGER;
        
        #         ALTER TABLE geo_umzr.tasks
        #             ADD CONSTRAINT fk_tasks_bpstr
        #             FOREIGN KEY (bpstr)
        #             REFERENCES geo_umzr.businessplanstr(id)
        #             ON DELETE CASCADE;
        #     """))

        # with engine.begin() as conn:
        #     conn.execute(text("""
        #         ALTER TABLE geo_umzr.businessplans
        #         ADD COLUMN IF NOT EXISTS project INTEGER
        #         REFERENCES geo_umzr.projects(id)
        #         ON DELETE CASCADE;
        #     """))

        
        # with engine.begin() as conn:
        #     conn.execute(text("""
        #         ALTER TABLE geo_umzr.businessplans
        #         ADD COLUMN IF NOT EXISTS parent INTEGER,
        #         ADD COLUMN IF NOT EXISTS doc VARCHAR;
        #     """))
        
        #     conn.execute(text("""
        #         ALTER TABLE geo_umzr.businessplans
        #         ADD CONSTRAINT fk_businessplans_parent
        #         FOREIGN KEY (parent)
        #         REFERENCES geo_umzr.businessplans(id)
        #         ON DELETE SET NULL;
        #     """))


        # Task.__table__.drop(engine)
        # PlanDateEnd.__table__.create(engine)
        # pds = session.query(PlanDateStart).filter_by(task=27, actual=True).order_by(PlanDateStart.id.desc()).first()
        # print(pds)
        # pds.actual = False
        # session.commit()

        # session.query(association_table_task_company).delete()
        # BusinessPlan.__table__.drop(engine)
        # session.query(BusinessPlan).delete()
        # session.query(BusinessPlanFacility).delete()
        # session.commit()
        # tasks = session.query(Task).all()
        # task = session.query(Task).filter(Task.id ==144).one_or_none()
        # session.delete(task)
        # session.commit()
        # task.divisions.clear()
        # session.commit()
        # print(task)
        # for t in tasks:
        #     print(f'Задача: {t.id} {t.name} {t.divisions}  {t.actual}')
        # Task.__table__.drop(engine)
        # BusinessPlan.__table__.create(engine)
        # # BusinessPlanFacility.__table__.create(engine)
        # session.commit()
        # with engine.connect() as conn:
        # #     conn.execute(text("DROP TABLE geo_umzr.tasks CASCADE"))
        #     conn.execute(text("DELETE FROM geo_umzr.tasks WHERE geo_umzr.tasks.id = 19"))
        # session.commit()
            #############################################################################
            #   1. Компания                                                             #
            #############################################################################
            # cmp1 = Company(name="Газпром нефть ПАО", full_name="Газпром нефть Публичное акционерное общество")
            # session.add(cmp1)
            # session.commit()
            # cmp2 = Company(name="ГПН-ГЕО ООО", full_name="Газпромнефть-ГЕО Общество с ограниченной ответственностью", parent=cmp1.id)
            # session.add(cmp2)
            # session.commit()

            #############################################################################
            #   2. Подразделения                                                        #
            #############################################################################
            # dvs1 = Division(name="Аппарат управления", abbr="АУП", company=cmp2.id)
            # session.add(dvs1)
            # session.commit()
            # dvs2 = Division(name="Управление маркшейдерско-землеустроительных работ", abbr="УМЗР", company=cmp2.id, parent=dvs1.id)
            # session.add(dvs2)
            # session.commit()
            #############################################################################
            #   3. Тип объекта                                                          #
            #############################################################################
            # ftype1 = FacilityType(name="Скважина")
            # ftype2 = FacilityType(name="Площадка")
            # session.add(ftype1)
            # session.add(ftype2)
            # session.commit()
    #############################################################################
    #   1. Компания                                                             #
    #############################################################################
    #   1.1. Создание                                                           #
    ############################################################################
        # cmp1 = Company(name="ГПН-ГЕО ООО", full_name="Газпромнефть-ГЕО Общество с ограниченной ответственностью")
        # session.add(cmp1)
        # session.commit()
    # cmp2 = Company(name="Газпром нефть ПАО", full_name="Газпром нефть Публичное акционерное общество", parent=cmp1.id)
    # session.add(cmp2)
    # session.commit()
        # cmps = session.query(Company).all()
        # for cmp in cmps:
        #     print(f"Company id: {cmp.id}, name: {cmp.name}, str: {cmp}")
    #############################################################################
    #   1.2. Подчиненность                                                      #
    #############################################################################
    # cmp1 = session.query(Company).filter_by(id=1).one_or_none()
    # cmp2 = session.query(Company).filter_by(id=2).one_or_none()
    # if cmp1 and cmp2:
    #     cmp1.parent = cmp2.id
    #     session.commit()
    # print(cmp1)
    #############################################################################
    #   1.3. Удаление головной                                                  #
    #############################################################################
    # # session.delete(cmp2)
    # # session.commit()
    # cmps = session.query(Company).all()
    # for cmp in cmps:
    #     print(f"Company id: {cmp.id}, name: {cmp.name}, str: {cmp}")
    #############################################################################
    #   2. Подразделения                                                        #
    #############################################################################
    #   2.1. Создание                                                           #
    #############################################################################
    # cmp2 = session.query(Company).filter_by(id=2).one_or_none()
    #     dvs1 = Division(name="Аппарат управления", abbr="АУП", company=cmp1.id)
    # # dvs3 = Division(name="Департамент управления имущественными отношениями", abbr="ДУИ", company=cmp2.id)
        # cmp1 = session.query(Company).filter_by(id=1).one_or_none()
        # dvs1 = session.query(Division).filter_by(id=6).one_or_none()
        # # print(dvs1)

        # dvs2 = Division(name="Управление проектно-изыскательских работ", abbr="УПИР", company=cmp1.id, parent=dvs1.id)
        # session.add(dvs2)
        # session.commit()
        # # print(dvs1)
        # divs = session.query(Division).all()
        # for div in divs:
        #     print(f"Division id: {div.id}, name: {div.name}, str: {div}")
    #############################################################################
    #   2.2. Подчиненность                                                      #
    #############################################################################
        # dvs2 = Division(name="Управление маркшейдерско-землеустроительных работ", abbr="УМЗР", company=cmp1.id, parent=dvs1.id)
        # # session.add_all([dvs1, dvs2])
        # session.add(dvs2)
        # session.commit()
    # print(dvs2)
    #############################################################################
    #   2.3. Удаление головной                                                  #
    #############################################################################
        # dvs1 = session.query(Division).filter_by(id=7).delete()
        # session.commit()
    #############################################################################
    #   3. Сотрудник                                                            #
    #############################################################################
    #   3.1. Создание                                                           #
    #############################################################################
            # cmp1 = session.query(Company).filter_by(id=2).one_or_none()
            # dvs2 = session.query(Division).filter_by(id=2).one_or_none()
            # # emp1 = Employee(name="Nastya", surname="Shevchenko", post="VS", company=cmp1.id, division=dvs2.id, login='Шевченко А.С.', password='2c8acbeb-631f-4fdf-9174-e96996264977')
            # emp2 = Employee(name="Евгений", surname="Горбунов", post="Начальник", company=cmp1.id, division=dvs2.id, login='Горбунов Е.А.', password='5193d077-4413-475f-9144-cac94a647715')

            # session.add(emp2)
            # session.commit()
    #############################################################################
    #   4. Удаление Компаний                                                    #
    #############################################################################
    # cmp1 = session.query(Company).filter_by(id=1).delete()
    # cmp2 = session.query(Company).filter_by(id=2).delete()

    #############################################################################
    #   4.1 Удаление Проектов (многие-ко-многим)                                #
    #############################################################################
        # session.execute(
        #     delete(association_table_license_project)
        #     .where(association_table_license_project.c.id_project == 5)
        # )
        # session.query(Project).filter_by(id=5).delete()
        # # proj1 = session.query(association_license_project).filter_by(id_project=5).delete() 
        # session.commit()


    #############################################################################
    #   5. Тест Лицензии - Проекты                                              #
    #############################################################################
    # cmp1 = Company(name="Газпром нефть ПАО", full_name="Газпром нефть Публичное акционерное общество")
    # session.add(cmp1)
    # session.commit()
    # cmp2 = Company(name="ГПН-ГЕО ООО", full_name="Газпромнефть-ГЕО Общество с ограниченной ответственностью", parent=cmp1.id)
    # session.add(cmp2)
    # session.commit()
    # lic1 = License(name='Южно-Новопортовский', dt_start='01.01.2020', dt_end='31.12.2030', company=cmp1.id)
    # lic2 = License(name='Суровый', dt_start='01.01.2020', dt_end='31.12.2030', company=cmp1.id)
    # session.add_all([lic1, lic2])
    # session.commit()
    # dvs1  = Division(name="Традиционные запасы", abbr="КТЗ", company=cmp2.id)
    # session.add(dvs1)
    # session.commit()
    # prj1 = Project(name="Южный Ямал", division=dvs1.id, licenses=[lic1, lic2])
    # session.add(prj1)
    # session.commit()
    # prj1 = session.get(Project, 1)  # Получаю проект с id=1
    # for lic in prj1.licenses:
    #     print(lic.id, lic.name)
    # projects = session.query(Project).all()
    # for project in projects:
    #     print(f'{project.name}')
    #     for lic in project.licenses:
    #         print(f'{lic.name}')

    #############################################################################
    #   6. Тест Задачи                                                          #
    #############################################################################
    # task1 = Task(name='test', status=TaskStatusEnum.WORKED, importance=TaskImportanceEnum.HIGH)
    # print(task1.name, task1.status, task1.importance)
    # session.add(task1)
    # session.commit()
    # tasks = session.query(Task).all()
    # for task in tasks:
    #     print(task.name, task.status.value, task.importance.value)
    #############################################################################
    #   7. Статьи затрат                                                        #
    #############################################################################
    #     costitem_1 = BusinessPlanCostItem(name='Аренда земли')
    #     costitem_2 = BusinessPlanCostItem(name='Возмещение убытков землепользователю')
    #     costitem_3 = BusinessPlanCostItem(name='Выполнение ЗУР')
    #     costitem_4 = BusinessPlanCostItem(name='Горный отвод')
    #     costitem_5 = BusinessPlanCostItem(name='Маркшейдерские работы')
    #     costitem_6 = BusinessPlanCostItem(name='Оформление прав собственности')
    #     costitem_7 = BusinessPlanCostItem(name='Рекультивация нарушенных земель')
    #     costitem_8 = BusinessPlanCostItem(name='Услуги по срочному трудовому договору или ГПХ')

    #     session.add_all([costitem_1, costitem_2, costitem_3, costitem_4, costitem_5, costitem_6, costitem_7, costitem_8])
    #     session.commit()
    # #############################################################################
    #   8. Этапы проекта                                                        #
    #############################################################################
        # projectstage_1 = ProjectStage(name='Поиск')
        # projectstage_2 = ProjectStage(name='Оценка')
        # projectstage_3 = ProjectStage(name='Выбор')

        # session.add_all([projectstage_1, projectstage_2, projectstage_3])
        # session.commit()

    #############################################################################
    #   9. Объект бизнес-плана                                                  #
    #############################################################################
            
    #     bpf_1 = BusinessPlanFacility(name='Скв.№1ПО Южно-Новопортовский ЛУ', project=3)
    #     session.add(bpf_1)
    #     session.commit()
    # #############################################################################
    # #   9. Строка Бизнес-плана                                                  #
    # #############################################################################
    #     bp_1 = session.query(BusinessPlan).filter_by(id=2).one_or_none()
    #     cmp_1 = session.query(Company).filter_by(id=2).one_or_none()
    #     # bpf_2 = session.query(BusinessPlanFacility).filter_by(id=1).one_or_none()
    #     costitem_1 = session.query(BusinessPlanCostItem).filter_by(id=1).one_or_none()
    #     stage_1 = session.query(ProjectStage).filter_by(id=1).one_or_none()
    #     facility_1 = session.query(Facility).filter_by(id=1).one_or_none()
    #     businessplanstr_1 = BusinessPlanStr(businessplan=bp_1.id,
    #                                         company=2,
    #                                         bpfacility=bpf_1.id,
    #                                         costitem=costitem_1.id,
    #                                         stage=stage_1.id,
    #                                         facility=3
    #                                        )

    #     session.add(businessplanstr_1)
    #     session.commit()
        # bp_1 = session.query(BusinessPlan).filter_by(id=1).delete()
        # bp_2 = session.query(BusinessPlan).filter_by(id=2).delete()
        # businessplanstr_1 = session.query(BusinessPlanStr).filter_by(id=1).delete()
        # session.commit()
        
# Session = sessionmaker(bind=engine)
# session = Session()
# cmp1 = Company(name="ГПН-ГЕО ООО", full_name="Газпромнефть-ГЕО Общество с ограниченной ответственностью")
# session.add(cmp1)
# session.commit()