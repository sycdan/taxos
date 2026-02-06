from pathlib import Path

from taxos import ACCESS_TOKENS_DIR


def get_token_file(key: str) -> Path:
  return ACCESS_TOKENS_DIR / f"{key}.json"
