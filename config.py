from dotenv import load_dotenv
import os

load_dotenv(override=True)

# Окружение Keycloak
KEYCLOAK_COOKIE_SECRET = os.environ.get('COOKIE_SECRET')
KEYCLOAK_CLIENT_ID = os.environ.get('CLIENT_ID')
KEYCLOAK_CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

SERVER_METADATA_URL = "https://app-sso.apps.stage.gazprom-neft.local/auth/realms/ai-platform/.well-known/openid-configuration"
REDIRECT_URL = "http://5d272a3f-ab90-4322-905c-3e0826e1cbbb-http.apps-spb.dha.paas.gazprom-neft.local/" #"https://brd007-ai-platform.apps.stage.gazprom-neft.local"
# REDIRECT_URL = "https://dev-22db318c-8303-4dc3-8be7-46275976903a-streamlit.apps.stage.gazprom-neft.local"
# REDIRECT_URL = "https://brd-geo-fin-dep-test.apps.stage.gazprom-neft.local" #"https://brd007-ai-platform.apps.stage.gazprom-neft.local"

# Доступ
ALLOWED_GROUP_PREFIXES = [
    "spb-paas-developer",
    "spb-paas-tester"
]

ALLOWED_USERS = ['gorbunov.eal',
                 'shevchenko.as',
                 'khokhlov.aa',
                 'fedorov.agen',
                 'rasulov.if',
                 'gorev.ma'
                ] #--------------------------Указываем логины кого пускать.