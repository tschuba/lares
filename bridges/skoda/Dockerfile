FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY skoda2mqtt.py .

RUN mkdir -p /app/logs

ENV PYTHONUNBUFFERED=1

CMD ["python", "skoda2mqtt.py"]
