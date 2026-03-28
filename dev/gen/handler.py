import inspect
import sys
from uuid import UUID

from dev import BACKEND_ROOT, FRONTEND_ROOT

sys.path.append(BACKEND_ROOT.as_posix())


def handle(command):
  from taxos import concepts

  output_path = FRONTEND_ROOT / "src/contracts.ts"

  lines = [
    "// Do not edit manually.",
    "// Run `dev.gen` to regenerate.",
    "",
  ]

  for name, value in inspect.getmembers(object=concepts):
    if name.startswith("_"):
      continue
    if not name.isupper():
      continue
    if isinstance(value, UUID):
      lines.append(f'export const {name} = "{value}";')

  lines.append("")
  output_path.write_text("\n".join(lines))
  print(f"✅ Generated {output_path}")
