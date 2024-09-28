FROM python:3.9.5-slim-buster

ARG DEBIAN_FRONTEND "noninteractive"
RUN apt-get update -y && apt-get upgrade -y && apt-get install ca-certificates ffmpeg brotli -y

RUN mkdir /app/
ADD . /app/
WORKDIR /app

RUN pip install pipenv==2023.3.20
RUN pipenv install --system --deploy

RUN apt-get install git -y

ENTRYPOINT [ "python", "-m", "src.main" ]
CMD []
