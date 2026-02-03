from dataclasses import dataclass


@dataclass
class TestApi:
  "Ensure the API container is working."

  use_proxy: bool = False
