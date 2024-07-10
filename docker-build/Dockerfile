from python:3.10-bullseye

RUN apt update
RUN apt install -y pandoc

RUN pip install --upgrade pip --no-cache-dir

RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH /root/.poetry/bin:$PATH
