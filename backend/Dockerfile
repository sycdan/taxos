FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy proto files and generate gRPC code
COPY protos/ ./protos/
RUN python -m grpc_tools.protoc \
    --proto_path=protos \
    --python_out=. \
    --grpc_python_out=. \
    protos/taxos_service.proto

# Copy application code
COPY . .

# Expose the gRPC port
EXPOSE 50051

# Run the server
CMD ["python", "server.py"]