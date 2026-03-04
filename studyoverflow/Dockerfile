FROM python:3.12-slim
RUN groupadd -r groupdjango && useradd -r -g groupdjango userdj

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip
WORKDIR /app/studyoverflow
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY new_requirements.txt .
RUN pip install -r new_requirements.txt

COPY . .

RUN mkdir -p /app/studyoverflow/celerybeat_data

RUN chown -R userdj:groupdjango /app/studyoverflow/celerybeat_data

USER userdj
