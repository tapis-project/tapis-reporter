FROM python:3.10-slim

ENV PYTHONUNBUFFERED=TRUE

EXPOSE 8000

WORKDIR /app
COPY ./requirements.txt /app

RUN pip install -r requirements.txt

COPY ./src/ /app

RUN python manage.py makemigrations
RUN python manage.py migrate
RUN python manage.py collectstatic --no-input