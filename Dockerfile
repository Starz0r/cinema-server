FROM python:3.9.5-slim-buster

RUN apt-get update && apt-get upgrade && apt-get install add ca-certificates ffmpeg brotli

RUN mkdir /app/
ADD . /app/
WORKDIR /app

RUN pip install pipenv==2023.3.20
RUN pipenv install --system --deploy

RUN apt-get install git

ENTRYPOINT [ "python", "-m src.main" ]
CMD []
