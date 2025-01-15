from dotenv import load_dotenv
import os

load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = int(os.getenv('DB_PORT'))
DB_NAME = os.getenv('DB_NAME')

TORTOISE_ORM = {
    'connections': {
        'default': f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    },
    'apps': {
        'models': {
            'models': [os.getenv('TORTOISE_ORM_MODELS')],
            'default_connection': 'default',
        },
        'aerich': {
            'models': [os.getenv('TORTOISE_ORM_AERICH_MODELS')],
            'default_connection': 'default',
        },
    },
    "use_tz": True,
    "timezone": "UTC",
}