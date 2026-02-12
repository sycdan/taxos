#!/usr/bin/env bash
rm -rf backend/data/tenants/0698940164917d1e80005b91d725b497/buckets/
rm -rf backend/data/tenants/0698940164917d1e80005b91d725b497/receipts/
docker compose up -d
docker exec -it taxos-frontend-1 npm run test:integration #-- -t "should handle receipt allocations correctly"
