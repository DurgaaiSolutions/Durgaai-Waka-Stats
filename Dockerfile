FROM python:3.13-alpine

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN mkdir -p /durgaai-waka-stats/assets

ADD requirements.txt /durgaai-waka-stats/requirements.txt
RUN apk add --no-cache g++ jpeg-dev zlib-dev libjpeg make git && pip3 install -r /durgaai-waka-stats/requirements.txt

RUN git config --global user.name "readme-bot"
RUN git config --global user.email "41898282+github-actions[bot]@users.noreply.github.com"

ADD sources/* /durgaai-waka-stats/
ENTRYPOINT cd /durgaai-waka-stats/ && python3 main.py
