PYTHON3=python3 
PIP=pip3 

FIXTURES_DIR=arts_api/fixtures
FNAME=app_`date +%m-%d-%Y_%H%M%S`

run: env
	. env/bin/activate; ${PYTHON3} manage.py runserver

env: env/bin/activate FORCE

env/bin/activate: requirements.txt
	test -d env || python3 -m venv env
	. env/bin/activate; ${PIP} install -Ur requirements.txt
	touch env/bin/activate

test: env
	. env/bin/activate; ${PYTHON3} manage.py test

migrate: env
	. env/bin/activate; ${PYTHON3} manage.py makemigrations; ${PYTHON3} manage.py migrate; 

# pass FNAME=fixture_filename to save into a different filename
fixture: env
	. env/bin/activate; ${PYTHON3} manage.py dumpdata --format=json --indent=4 > ${FIXTURES_DIR}/${FNAME}.json

schema: env
	. env/bin/activate; ${PYTHON3} manage.py generateschema > openapi-schema.yml

clean:
	rm -rf env
	find -iname "*.pyc" -delete

reset: clear migrate

clear:
	rm -rf data
	rm db.sqlite3

FORCE:
