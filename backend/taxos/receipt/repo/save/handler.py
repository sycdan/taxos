import pickle

from taxos.context.tools import require_tenant
from taxos.receipt.repo.save.command import SaveReceiptRepo
from taxos.receipt.tools import get_repo_file


def handle(command: SaveReceiptRepo):
  tenant = require_tenant()
  repo_file = get_repo_file(tenant.guid)
  repo_file.parent.mkdir(parents=True, exist_ok=True)
  temp_file = repo_file.with_suffix(".tmp")
  pickle.dump(command.repo, open(temp_file, "wb"))
  temp_file.replace(repo_file)
