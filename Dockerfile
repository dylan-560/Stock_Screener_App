FROM python:3.9.16-alpine3.16
ENV PYTHONUNBUFFERED 1  # prints any outputs directly the console

WORKDIR /app


RUN yes | apt-get install python3-dev default-libmysqlclient-dev build-essential -y
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .

EXPOSE 8000

CMD python manage.py runserver