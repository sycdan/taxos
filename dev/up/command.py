from dataclasses import dataclass


@dataclass
class Up:
  "Start a development server."

  build: bool = True
  no_watch: bool = False
