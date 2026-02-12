import hashlib
import shutil
import zipfile
from pathlib import Path

import pytest
from taxos.access.token.generate.command import GenerateAccessToken
from taxos.access.token.revoke.command import RevokeToken
from taxos.context.entity import Context
from taxos.context.tools import set_context
from taxos.receipt.attach_file.command import AttachFile
from taxos.receipt.create.command import CreateReceipt
from taxos.receipt.entity import Receipt
from taxos.receipt.repo.load.command import LoadReceiptRepo
from taxos.tenant.create.command import CreateTenant
from taxos.tenant.delete.command import DeleteTenant
from taxos.tenant.entity import TenantRef
from taxos.tenant.tools import get_files_dir
from taxos.tools import guid


@pytest.fixture
def test_context():
  """Create a test tenant and generate access token, cleanup after test"""
  tenant = CreateTenant(name="Test Tenant").execute()
  access_token = GenerateAccessToken(tenant).execute()
  context = Context(tenant, access_token)
  set_context(context)

  yield context

  # Cleanup
  try:
    RevokeToken(hash=access_token.key).execute()
    DeleteTenant(TenantRef(tenant.guid.hex)).execute()
  except Exception as e:
    print(f"Cleanup warning: {e}")


def test_attach_file_to_receipt(test_context, tmp_path):
  tenant = test_context.tenant

  # 1. Create a dummy receipt
  receipt = CreateReceipt(
    vendor="Test Vendor",
    total=100.0,
    date="2023-10-27T10:00:00",
    timezone="UTC",
  ).execute()

  # 2. Create a dummy file
  test_file_content = b"This is a test file content."
  test_file_path = tmp_path / "test_file.txt"
  test_file_path.write_bytes(test_file_content)

  # Calculate expected hash
  expected_hash = hashlib.sha256(test_file_content).hexdigest()

  # 3. Execute AttachFile command
  updated_receipt = AttachFile(receipt.guid.hex, test_file_path).execute()

  # 4. Verify receipt hash
  assert updated_receipt.hash == expected_hash
  assert updated_receipt.guid == receipt.guid

  # Verify persistence
  repo = LoadReceiptRepo().execute()
  persisted_receipt = repo.get_by_ref(receipt.guid)
  assert persisted_receipt.hash == expected_hash

  # 5. Verify file storage
  files_dir = get_files_dir(tenant.guid)
  zip_path = files_dir / f"{expected_hash}.zip"
  assert zip_path.exists()

  # 6. Verify zip content
  with zipfile.ZipFile(zip_path, "r") as zipf:
    assert test_file_path.name in zipf.namelist()
    extracted_content = zipf.read(test_file_path.name)
    assert extracted_content == test_file_content

  # 7. Error should be raised if we try to attach another file
  another_test_file_path = tmp_path / "another_test_file.txt"
  another_test_file_path.write_bytes(b"Another test file content.")
  with pytest.raises(FileExistsError):
    AttachFile(receipt.guid.hex, another_test_file_path).execute()