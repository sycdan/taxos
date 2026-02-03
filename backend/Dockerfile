FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git g++ make && rm -rf /var/lib/apt/lists/*

COPY ./backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt

# Copy necessary source directories
COPY ./backend/api/ ./api/
COPY ./backend/taxos/ ./taxos/

# Copy proto files and generate protobuf code
COPY ./proto/ ./proto/
RUN find ./proto -name "*.proto" -exec python -m grpc_tools.protoc \
  --proto_path=proto \
  --python_out=./api \
  --grpc_python_out=./api \
  --pyi_out=./api \
  {} \; && \
  rm -rf ./proto/

ENV PYTHONPATH=/app

EXPOSE 50051

CMD ["python", "api/main.py"]
