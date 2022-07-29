PYTHON3=python3 
PIP=pip3

run: env
	mkdir -p log
	. env/bin/activate
	${PYTHON3} manage.py runserver

env: env/bin/activate

env/bin/activate: requirements.txt
	test -d env || python3 -m venv env
	. env/bin/activate
	${PIP} install -r requirements.txt
	${PIP} install -r libsilverline/requirements.txt
	touch env/bin/activate

migrate: env
	. env/bin/activate
	${PYTHON3} manage.py makemigrations
	${PYTHON3} manage.py migrate

clean:
	rm -rf env
	find -iname "*.pyc" -delete

reset: clear migrate

clear:
	rm -f db.sqlite3
	rm -rf log
