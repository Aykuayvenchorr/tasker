import time
import streamlit as st
from utils.helpers import Helpers
from services.service_comment import ServiceComment
from services.service_auth import ServiceAuth


class UiComment:
    """Класс работы с комментариями"""

    @staticmethod
    def render_comments_block(obj) -> None:
        """Отображение блока комментариев"""
        st.divider()
        with st.expander(label='Комментарии', icon=':material/forum:'):
            comment_col1_btn, comment_col2_btn, comment_col3_btn = st.columns([1, 1, 7])
            if comment_col1_btn.button('Добавить', width='stretch', key='comment_btn_add'):
                field = ServiceComment.get_field_from_object(obj)
                st.session_state.comment_show_form_add = True
                UiComment.render_dialog_comment_add(field, obj.id)
            comments = ServiceComment.get_comments(obj)
            for comment in comments:
                UiComment.render_comment(comment)


    @staticmethod
    @st.dialog(title="Добавление комментария",
               width="large",
               dismissible=False,
               on_dismiss="ignore",
               icon=':material/forum:')
    def render_dialog_comment_add(field: str, pk: int, parent: int|None = None) -> None:
        """Диалоговое окно добвления Комментария"""
        if st.session_state.comment_show_form_add:
            name = st.text_input(label='Краткое содержание')
            full_name = st.text_area('Текст комментария')
            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 7])
            if btn_col1.button('Сохранить', width='stretch'):
                ServiceComment.db_comment_insert(name, full_name, parent, field, pk, st.session_state.employee.id)
                Helpers.form_close('comment_show_form_add')
            if btn_col2.button('Отменить', width='stretch'):
                Helpers.form_close('comment_show_form_add')


    @staticmethod
    def render_comment(obj) -> None:
        """Отображение одного комментария"""
        employee = ServiceAuth.get_employee__id(obj.employee_created)
        with st.expander(label=f'{obj.created_at.strftime("%d.%m.%Y %H:%M")} / {employee.surname} {employee.name}: {obj.name}', icon=':material/forum:'):
            st.text(obj.full_name)
            if st.button('Прокомментировать', key=f'btn_subcomment_{obj.id}'):
                st.session_state.comment_show_form_add = True
                UiComment.render_dialog_comment_add(None, None, obj.id)
            children = ServiceComment.get_comment_children(obj)
            if len(children) > 0:
                for child in children:
                    UiComment.render_comment(child)
            
            