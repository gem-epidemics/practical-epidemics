from python:3.10-bullseye

RUN apt update
RUN apt install -y pandoc

RUN pip install --upgrade pip --no-cache-dir

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python

ENV PATH /root/.poetry/bin:$PATH
