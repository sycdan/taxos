FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git g++ make && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt

COPY ./api/ ./api/
COPY ./taxos/ ./taxos/

ENV PYTHONPATH=/app

EXPOSE 50051

CMD ["python", "api/connect_http_server.py"]
