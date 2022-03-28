FROM python:3

WORKDIR /usr/src/app

COPY arts-main/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

WORKDIR /usr/src/app/arts-main

RUN chmod +x wait-for-it.sh
RUN chmod +x docker-entrypoint.sh

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD python manage.py runserver 0.0.0.0:8000
