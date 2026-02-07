from dataclasses import dataclass


@dataclass
class TestApi:
  "Ensure the gRPC API server is working."

  no_integration: bool = False
