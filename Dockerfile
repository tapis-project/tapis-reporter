FROM python:3.10-slim

ENV PYTHONUNBUFFERED=TRUE

EXPOSE 8000

WORKDIR /app
COPY ./requirements.txt /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip uninstall pycrypto
RUN pip install pycryptodome
RUN apt-get update
RUN apt-get install -y build-essential
RUN pip install splunklib

COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# COPY ./init_db.sh /init_db.sh
# RUN chmod +x /init_db.sh

COPY ./src/ /app

# ENTRYPOINT ["./entrypoint.sh"]
#RUN python manage.py makemigrations
#RUN python manage.py migrate
#RUN python manage.py collectstatic --no-input
#RUN python init_db.py