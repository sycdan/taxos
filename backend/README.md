# TaxOS Backend

A gRPC-based Python backend for the TaxOS receipt tracking application.

## Features

- **gRPC API** for high-performance communication with the UI
- **SQLite database** for persistent storage
- **Bucket management** - organize expenses into categories
- **Receipt tracking** - store receipt details with amounts and dates
- **Dashboard analytics** - get summaries and totals by date range
- **Docker support** for easy deployment

## API Overview

The backend provides the following gRPC services:

### Bucket Operations
- `CreateBucket` - Create a new expense bucket
- `GetBucket` - Get bucket by ID
- `ListBuckets` - List all buckets with summaries
- `UpdateBucket` - Update bucket details
- `DeleteBucket` - Delete a bucket

### Receipt Operations
- `CreateReceipt` - Add a new receipt to a bucket
- `GetReceipt` - Get receipt by ID
- `ListReceipts` - List receipts for a bucket with filtering
- `UpdateReceipt` - Update receipt details
- `DeleteReceipt` - Delete a receipt

### Dashboard
- `GetDashboard` - Get dashboard summary with totals

## Quick Start

### Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate gRPC code:**
   ```bash
   python -m grpc_tools.protoc \
     --proto_path=protos \
     --python_out=. \
     --grpc_python_out=. \
     protos/taxos_service.proto
   ```

3. **Run the server:**
   ```bash
   python server.py
   ```

The server will start on `localhost:50051`.

### Docker

1. **Build the image:**
   ```bash
   docker build -t taxos-backend .
   ```

2. **Run the container:**
   ```bash
   docker run -p 50051:50051 -v ./data:/app/data taxos-backend
   ```

### Using with docker-compose

From the parent directory:
```bash
docker compose up
```

## Database Schema

The backend uses SQLite with the following tables:

### Buckets
- `id` (TEXT PRIMARY KEY) - UUID
- `name` (TEXT NOT NULL) - Display name
- `description` (TEXT) - Optional description
- `created_at` (INTEGER) - Timestamp in milliseconds
- `updated_at` (INTEGER) - Timestamp in milliseconds

### Receipts
- `id` (TEXT PRIMARY KEY) - UUID
- `bucket_id` (TEXT NOT NULL) - Foreign key to buckets
- `description` (TEXT NOT NULL) - Receipt description
- `amount` (REAL NOT NULL) - Amount in dollars
- `date` (INTEGER NOT NULL) - Receipt date in milliseconds
- `image_url` (TEXT) - Optional path to receipt image
- `metadata` (TEXT) - JSON blob for additional data
- `created_at` (INTEGER) - Timestamp in milliseconds
- `updated_at` (INTEGER) - Timestamp in milliseconds

## Configuration

Environment variables:
- `DB_PATH` - Path to SQLite database file (default: `taxos.db`)

## Testing the API

You can test the gRPC API using a tool like [grpcurl](https://github.com/fullstorydev/grpcurl):

```bash
# List available services
grpcurl -plaintext localhost:50051 list

# Create a bucket
grpcurl -plaintext -d '{"name": "Office Supplies", "description": "Pens, paper, etc."}' \
  localhost:50051 taxos.TaxosService/CreateBucket

# Get dashboard
grpcurl -plaintext -d '{"include_empty_buckets": true}' \
  localhost:50051 taxos.TaxosService/GetDashboard
```