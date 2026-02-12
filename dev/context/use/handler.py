from backend.taxos.context.tools import get_default_context_file, require_tenant
from backend.taxos.tools import json
from dev.context.use.command import UseContext


def handle(command: UseContext):
  tenant = require_tenant(command.tenant)
  context_file = get_default_context_file()
  context = json.load(context_file)
  context["tenant"] = tenant.guid
  json.dump(context, context_file)
  return command.tenant
