import os
import streamlit as st
from typing import List
from streamlit.runtime.secrets import secrets_singleton

from config import REDIRECT_URL, KEYCLOAK_COOKIE_SECRET, KEYCLOAK_CLIENT_ID, KEYCLOAK_CLIENT_SECRET, \
    SERVER_METADATA_URL, ALLOWED_GROUP_PREFIXES, ALLOWED_USERS
from logger import app_logger


def setup_auth_env():
    """Установка переменных окружения и auth-конфига."""
    os.environ["REDIRECT_URL"] = REDIRECT_URL
    os.environ["KEYCLOAK_COOKIE_SECRET"] = KEYCLOAK_COOKIE_SECRET
    os.environ["KEYCLOAK_CLIENT_ID"] = KEYCLOAK_CLIENT_ID
    os.environ["KEYCLOAK_CLIENT_SECRET"] = KEYCLOAK_CLIENT_SECRET
    os.environ["SERVER_METADATA_URL"] = SERVER_METADATA_URL

    secrets_singleton._secrets = {
        "auth": {
            "redirect_uri": f"{REDIRECT_URL}/oauth2callback",
            "cookie_secret": KEYCLOAK_COOKIE_SECRET,
            "client_id": KEYCLOAK_CLIENT_ID,
            "client_secret": KEYCLOAK_CLIENT_SECRET,
            "server_metadata_url": SERVER_METADATA_URL,
            "client_kwargs": {"verify": False}
        }
    }


def authenticate_user() -> bool:
    """Основная проверка пользователя. Возвращает True если пользователь допущен."""
    if not st.user.is_logged_in:
        st.login()
        return False

    user_info = st.user.to_dict()
    st.session_state.user_info = st.user
    username = st.user.preferred_username
    roles: List[str] = user_info.get("role", [])

    app_logger.info("Пользователь успешно аутентифицирован", extra={
        "session_state": st.user.session_state,
        "user": username,
    })

    has_allowed_role = any(
        any(role.startswith(prefix) for prefix in ALLOWED_GROUP_PREFIXES)
        for role in roles
    )

    is_allowed_user = username in ALLOWED_USERS

    if not (is_allowed_user): #--------------- НЕ МЕНЯТЬ has_allowed_role or - для пользователей имеющих определенную роль на дата-платформе
        app_logger.warning("Доступ запрещён", extra={
            "session_state": st.user.session_state,
            "user": username,
        })
        st.error("⛔️ У вас нет доступа к приложению.")
        st.stop()
    # st.markdown(f"👤 {username}")
    # st.markdown(f"👤 {st.user.given_name}, добрый день!")
    return True
