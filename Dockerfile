FROM python:3.12-slim

WORKDIR /app

# Install git and build tools for dependencies
RUN apt-get update && apt-get install -y git g++ make && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy necessary source directories
COPY api/ ./api/
COPY taxos/ ./taxos/

ENV PYTHONPATH=/app

EXPOSE 50051

CMD ["python", "api/main.py"]
