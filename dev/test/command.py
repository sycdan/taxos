from dataclasses import dataclass


@dataclass
class Test:
  "Ensure the domain logic is working."

  no_integration: bool = False
  no_frontend: bool = False
