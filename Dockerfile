FROM python:3

WORKDIR /usr/src/app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN git clone https://github.com/SilverLineFramework/libsilverline.git || true # dont error out when libsilverline folder exists
WORKDIR /usr/src/app/libsilverline
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /usr/src/app

#ENTRYPOINT ["./docker-entrypoint.sh"]
CMD python manage.py runserver 0.0.0.0:8000
