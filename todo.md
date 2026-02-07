# Today's Task - Tenant Support

## Tenant Infrastructure (Core)

- [x] Create Tenant entity and domain
- [x] Create CreateTenant action
- [x] Create LoadTenant query
- [x] Create AccessToken entity
- [x] Create AuthenticateTenant action
- [x] Create GenerateAccessToken action
## Update ConnectRPC API to check access tokens in headers

- [x] Add @require_auth decorator to all endpoints
- [x] Extract token from Authorization header (Bearer format)
- [x] Call AuthenticateTenant to validate token
- [x] Return 401 for invalid/missing tokens
- [x] Store tenant in request context
- [x] Create dev/tenant_setup action for testing
- [x] Test tenant creation and token generation

## Move Buckets/Receipts Under Tenants

- [x] Update bucket storage paths to be under tenants
- [x] Update receipt storage paths to be under tenants
- [x] Update all bucket handlers to accept tenant context
- [x] Update all receipt handlers to accept tenant context
- [x] Update ListBuckets to filter by tenant
- [x] Test CRUD operations still work

## Frontend Integration

- [x] Add access token input to frontend
- [x] Store token in localStorage
- [x] Send token in API request headers
- [x] Handle 401 responses
- [x] Add logout button to UI

## ✅ COMPLETE - All tenant support functionality is now fully implemented!

## Architecture Notes

Per the requirements:
- Tokens are SHA256(guid + token_count)
- Initial token: SHA256(guid + 0) for first generation
- When new token requested: increment token_count, generate new hash, delete old token file
- API checks token header first, returns 401 if invalid
- Developers control access (no signup process)

---

## Original Task Description

We need to add a Tenant domain & entity. (./backend/taxos/tenant/entity.py)

We need a CreateTenant action that a developer can use to add a Tenant to the system.

This will create a folder in backend/data/tenants/<tenant_guid>

Once we have a tenant domain, we can move the bucket and receipt domains into it, and then ensure the app still works with its current level of functionality (basically just CRUD on buckets) befor we add anything new.

In order to access data, users of the frontend will need to provide an access token.
They will enter it once and then it will be stored in local storage.

On the backend, Acesst Tokens (backend/taxos/access/token/entity.py) will be stored in data/access_tokens/<hash>.json

The file will contain an object with a "tenant_ref" property (of TenantRef type on the entity dataclass).

The grpc connect API will check for an access token in the request headers first.
It will attempt to use the AuthenticateTenant(token_hash).execute() action to find the tenant. If that raises, it will return 401 to the user. The action will look for a matching json file in the access token data folder. If it finds one, it will load the json into a dict, get the tenant ref into a TenantRef entity object and then hydrate it, returning the resulting Tenant.

A token will simply be a sha256 string (starts out as a hash of the tenant guid + 0). When a new one is requested, we will incrememnt the token_count in the tenant and regenerate the tkoen based on guid + token_count. The old access token file will be deleted. The token is effectively a user password, but it will not be chosen by them (we don't want people using memorable passwords, since they are insecure by nature).

Developers will control who gains access for now -- there is no signup process (this is an internal-use tool).
