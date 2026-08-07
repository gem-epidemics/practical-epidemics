from python:3.10-bullseye

RUN apt update
RUN apt install -y pandoc

RUN pip install --upgrade pip --no-cache-dir

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH /root/.local/bin:$PATH
