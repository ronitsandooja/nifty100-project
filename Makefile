install:
	pip install -r requirements.txt

test:
	pytest tests/

load:
	python -m src.etl.loader

clean:
	rm -rf __pycache__
