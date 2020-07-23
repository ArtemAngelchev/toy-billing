FROM python:3.8 AS release

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

EXPOSE 5000

COPY requirements.release .
RUN pip install -r requirements.release

COPY . .

RUN mkdir -p /usr/src/app/tests/coverage
RUN chmod -R 777 /usr/src/app/tests/coverage

ENTRYPOINT ["gunicorn", "-c=python:gunicorn_conf", "src:create_app()"]


FROM release AS local

RUN pip install -r requirements.local
