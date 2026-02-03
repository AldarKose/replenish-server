FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends cron tzdata \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY worker_run.py /app/worker_run.py
COPY crontab /etc/cron.d/replenish-cron

RUN chmod 0644 /etc/cron.d/replenish-cron \
  && crontab /etc/cron.d/replenish-cron \
  && touch /var/log/worker.log

CMD ["cron", "-f"]

