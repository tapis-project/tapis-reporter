FROM python:3.10-slim

ENV PYTHONUNBUFFERED=TRUE

EXPOSE 8000

WORKDIR /app
COPY ./requirements.txt /app

RUN pip install -r requirements.txt

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY init_db.sh /init_db.sh
RUN chmod +x /init_db.sh

COPY ./src/ /app
