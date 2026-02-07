from dataclasses import dataclass


@dataclass
class TestApi:
  "Ensure the gRPC API server is working."

  port: int = 50051
  timeout: int = 30
  nuke_data: bool = False
