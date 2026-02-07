import logging

from taxos.access.token.revoke.command import RevokeToken
from taxos.access.token.tools import get_token_file

logger = logging.getLogger(__name__)


def handle(command: RevokeToken):
  logger.debug(f"Handling {command}")
  token = get_token_file(command.hash)
  if token.exists():
    logger.info(f"Revoking access token with hash {command.hash}")
    token.unlink()
    return True
  logger.info("Access token with hash {command.hash} not found")
  return False
