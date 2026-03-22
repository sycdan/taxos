import json
import sys
import uuid

sys.path.append("./backend")

from taxos import ACCESS_TOKENS_DIR, DATA_DIR, TENANTS_DIR

from dev.seed.command import Seed


def print_access_token():
  token = next(ACCESS_TOKENS_DIR.iterdir())
  print(f"🗝️  Your access token is: {token.stem}")


def handle(command: Seed):
  print("🌱 Seeding data...")
  DATA_DIR.mkdir(exist_ok=True, parents=True)

  default_context_file = DATA_DIR / "default_context.json"
  if default_context_file.exists():
    print("⚠️  Dev environment already seeded. Skipping.")
    print("💡 Run dev.nuke if you want to start over.")
    return print_access_token()

  tenant_guid = uuid.uuid4().hex
  tenant_dir = TENANTS_DIR / tenant_guid
  tenant_dir.mkdir(exist_ok=True, parents=True)
  tenant_state_file = tenant_dir / "state.json"
  with open(tenant_state_file, "w") as f:
    json.dump({"name": "Taxos Dev"}, f)

  with open(default_context_file, "w") as f:
    json.dump({"tenant": tenant_guid}, f)

  ACCESS_TOKENS_DIR.mkdir(exist_ok=True, parents=True)
  token = uuid.uuid4().hex
  token_file = ACCESS_TOKENS_DIR / f"{token}.json"
  with token_file.open("w") as f:
    json.dump({"tenant": tenant_guid}, f)

  print("✅ Dev environment seeded.")
  return print_access_token()
