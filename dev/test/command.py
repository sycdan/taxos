from dataclasses import dataclass


@dataclass
class Test:
  "Ensure the domain logic is working."

  test_pattern: str = ""
  no_integration: bool = False
