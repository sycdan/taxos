#!/usr/bin/env bash

# curl -X POST localhost:50051/taxos.v1.TaxosApi/DownloadReceiptFile \
#   -d '{"file_hash": "82417b733bf20cb84e37acab7bf5e0f82307765619d6b1e72594b68b131c6931c"}' \
#   -H "content-type:application/json" \
#   -H "Authorization: Bearer ce476040807e4c8699478226d3a0c8ebaaf1a79157278b2740f4ea95fb43b58d"

# rm -rf backend/data/tenants/0698940164917d1e80005b91d725b497/buckets/
# rm -rf backend/data/tenants/0698940164917d1e80005b91d725b497/receipts/
# docker compose up -d
# cd frontend
# npm run test:integration #-- -t "should handle receipt allocations correctly"
