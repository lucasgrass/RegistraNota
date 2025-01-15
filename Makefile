PROJECT_NAME = app.main:app
HOST = 0.0.0.0
PORT = 8000


install:
		pip install -r requirements.txt


freeze:
		pip freeze > requirements.txt


run:
		uvicorn $(PROJECT_NAME) --host $(HOST) --port $(PORT) --reload


test:
		pytest


clean:
		rm -rf __pycache__ .pytest_cache
