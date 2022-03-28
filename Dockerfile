FROM python:3

WORKDIR /usr/src/app

COPY arts-main/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

WORKDIR /usr/src/app/arts-main

RUN chmod +x wait-for-it.sh

RUN python manage.py makemigrations --noinput --merge
RUN python manage.py migrate

ENTRYPOINT ["/usr/src/app/arts-main/docker-entrypoint.sh"]
CMD python manage.py runserver 0.0.0.0:8000
