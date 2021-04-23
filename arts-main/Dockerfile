FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x wait-for-it.sh

RUN python manage.py makemigrations --noinput --merge
RUN python manage.py migrate
RUN rm -fr public
RUN python manage.py collectstatic

CMD python manage.py runserver 0.0.0.0:8000
