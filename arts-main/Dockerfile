FROM python:3-buster

WORKDIR /usr/src/app

# extra dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
		wait-for-it \
	&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py makemigrations --noinput
RUN python manage.py migrate
RUN rm -fr public
RUN python manage.py collectstatic

CMD python manage.py runserver 0.0.0.0:8000
