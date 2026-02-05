# Taxos development task list

## Buckets

These domain actions must be hooked up to GRPC endpoints:

- [x] create bucket domain action
- [x] create bucket grpc endpoint
- [x] update bucket domain action
- [x] update bucket grpc endpoint
- [x] delete bucket domain action
- [x] delete bucket grpc endpoint
- [x] list buckets domain action
- [x] list buckets grpc endpoint

## Receipts

- [x] create receipt domain action (manual, no source file)
  - [x] add proto service definition
  - [x] generate protos (dev.gen-proto)
  - [x] add an integration test that calls our grpc server to create a receipt
  - [x] ensure frontend client is hooked up
- [ ] ingest receipt domain action (save source file)
