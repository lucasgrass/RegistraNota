from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

TORTOISE_ORM = {
    'connections': {
        'default': DATABASE_URL,
    },
    'apps': {
        'models': {
            'models': ['app.models'],
            'default_connection': 'default',
        },
        'aerich': {
            'models': ['aerich.models'],
            'default_connection': 'default',
        },
    },
    "use_tz": True,
    "timezone": "America/Sao_Paulo",
}