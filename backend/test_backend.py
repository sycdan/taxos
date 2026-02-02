#!/usr/bin/env python3
"""
Simple test script to verify TaxOS backend components work.
"""

import sqlite3
import sys
import uuid
from pathlib import Path


def test_database():
  """Test SQLite database creation and basic operations."""
  print("🔍 Testing database operations...")

  db_path = "test_taxos.db"

  try:
    # Test database creation
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create test tables
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS buckets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )
        """)

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id TEXT PRIMARY KEY,
                bucket_id TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                date INTEGER NOT NULL,
                image_url TEXT,
                metadata TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                FOREIGN KEY (bucket_id) REFERENCES buckets (id)
            )
        """)

    # Test insert
    bucket_id = str(uuid.uuid4())
    now = 1706832000000  # Test timestamp

    cursor.execute(
      """
            INSERT INTO buckets (id, name, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """,
      (bucket_id, "Test Bucket", "Test Description", now, now),
    )

    # Test read
    cursor.execute("SELECT * FROM buckets WHERE id = ?", (bucket_id,))
    result = cursor.fetchone()

    if result:
      print(f"✅ Database test passed! Created bucket: {result[1]}")
    else:
      print("❌ Database test failed - no bucket found")
      return False

    conn.commit()
    conn.close()

    # Clean up
    Path(db_path).unlink(missing_ok=True)

    return True

  except Exception as e:
    print(f"❌ Database test failed: {e}")
    return False


def test_grpc_imports():
  """Test that gRPC dependencies can be imported."""
  print("📦 Testing gRPC imports...")

  try:
    import grpc

    print("✅ grpc imported successfully")

    import grpc.aio

    print("✅ grpc.aio imported successfully")

    from grpc_tools import protoc

    print("✅ grpc_tools imported successfully")

    return True

  except ImportError as e:
    print(f"❌ gRPC import failed: {e}")
    return False


def test_generated_code():
  """Test that generated gRPC code can be imported."""
  print("🤖 Testing generated gRPC code...")

  try:
    import taxos_service_pb2

    print("✅ taxos_service_pb2 imported successfully")

    import taxos_service_pb2_grpc

    print("✅ taxos_service_pb2_grpc imported successfully")

    # Test message creation
    bucket = taxos_service_pb2.Bucket(
      id="test-id",
      name="Test Bucket",
      description="Test Description",
      created_at=1706832000000,
      updated_at=1706832000000,
    )

    print(f"✅ Created test bucket message: {bucket.name}")

    return True

  except ImportError as e:
    print(f"❌ Generated code import failed: {e}")
    print(
      "   Make sure to run: python -m grpc_tools.protoc --proto_path=protos --python_out=. --grpc_python_out=. protos/taxos_service.proto"
    )
    return False


def main():
  """Run all tests."""
  print("🧪 TaxOS Backend Test Suite")
  print("=" * 40)

  tests = [test_grpc_imports, test_generated_code, test_database]

  passed = 0
  for test in tests:
    if test():
      passed += 1
    print()

  print(f"📊 Test Results: {passed}/{len(tests)} tests passed")

  if passed == len(tests):
    print("🎉 All tests passed! Your backend setup is working.")
    return 0
  else:
    print("⚠️  Some tests failed. Check the output above.")
    return 1


if __name__ == "__main__":
  sys.exit(main())
