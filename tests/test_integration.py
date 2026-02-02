def test_all(scaf):
  bucket_name = "test bucket"

  response = scaf("taxos/bucket/create", [bucket_name])
  assert response["name"] == bucket_name
  bucket_guid = response["guid"]

  response = scaf("taxos/bucket/update", [bucket_guid, f"{bucket_name}-updated"])
  assert response["name"] == f"{bucket_name}-updated"

  response = scaf("taxos/bucket/load", [bucket_guid])
  assert response["guid"] == bucket_guid

  # Delete the bucket, should return True for successful deletion
  response = scaf("taxos/bucket/delete", [bucket_guid])
  assert response is True

  # Delete a second time to ensure it returns False (no fail, just not deleted)
  response = scaf("taxos/bucket/delete", [bucket_guid])
  assert response is False
