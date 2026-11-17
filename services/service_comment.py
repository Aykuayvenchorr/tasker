from typing import List
from models import SessionLocal, Comment


class ServiceComment():
    """Сервис работы с комментариями"""

    @staticmethod
    def get_field_from_object(obj) -> str:
        """Получение наименования поля в комментарии, по типу объекта"""
        if obj.__class__.__name__ == "Company":
            return 'company'
        if obj.__class__.__name__ == "Division":
            return 'division'
        if obj.__class__.__name__ == "Project":
            return 'project'
        if obj.__class__.__name__ == "License":
            return 'license'
        if obj.__class__.__name__ == "Facility":
            return 'facility'
        if obj.__class__.__name__ == "Task":
            return 'task'


    @staticmethod
    def db_comment_insert(name, full_name, parent, field, pk, employee_id) -> bool:
        """Добавление комментария"""
        db = SessionLocal()
        try:
            comment = Comment(name=name, full_name=full_name, parent=parent, employee_created=employee_id)
            if field != None:
                setattr(comment, field, pk)
            db.add(comment)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f'Ошибка добавления комментария: {e}')
            return False
        finally:
            db.close()

    @staticmethod
    def get_comments(obj) -> List[Comment]:
        """Получение всех комментариев объекта"""
        db = SessionLocal()
        try:
            field = ServiceComment.get_field_from_object(obj)
            comments = db.query(Comment).filter(getattr(Comment, field) == obj.id)
            comments = comments.filter(Comment.parent.is_(None)).all()
            return comments
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения комментариев: {e}')
            return None
        finally:
            db.close()

    @staticmethod
    def get_comment_children(obj):
        """Получение дочерних комментариев у родительского комментария"""
        db = SessionLocal()
        try:
            children = db.query(Comment).filter(Comment.parent == obj.id).all()
            return children
        except Exception as e:
            db.rollback()
            print(f'Ошибка получения дочерних комментариев: {e}')
            return None
        finally:
            db.close()