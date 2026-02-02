from pathlib import Path
from taxos.receipt.ingest.command import IngestCommand

ACTION_DIR = Path(__file__).parent
TEMPLATES_DIR = ACTION_DIR / "templates"

def handle(command: IngestCommand):
  raise NotImplementedError("IngestCommand handler is not implemented yet.")