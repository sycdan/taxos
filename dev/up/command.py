from dataclasses import dataclass

@dataclass
class Up:
  "Start a development server."
  no_watch: bool = False
