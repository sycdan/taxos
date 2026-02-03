from dataclasses import dataclass


@dataclass
class Serve:
  "Start a development server."

  no_watch: bool = False
