FROM python:3

WORKDIR /usr/src/app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN git clone https://github.com/SilverLineFramework/libsilverline.git
#COPY libsilverline/requirements.txt ./
WORKDIR /usr/src/app/libsilverline
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /usr/src/app

RUN chmod +x wait-for-it.sh
RUN chmod +x docker-entrypoint.sh

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD python manage.py runserver 0.0.0.0:8000
