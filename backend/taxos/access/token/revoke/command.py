from dataclasses import dataclass


@dataclass
class RevokeToken:
  hash: str

  def execute(self):
    from taxos.access.token.revoke.handler import handle

    return handle(self)
