import logging
import os

from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

_driver = None


def get_driver():
  global _driver
  if _driver is None:
    uri = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
    auth = (
      os.environ.get("NEO4J_USER", "neo4j"),
      os.environ.get("NEO4J_PASSWORD", "password"),
    )
    logger.info("Connecting to Neo4j at %s", uri)
    _driver = GraphDatabase.driver(uri, auth=auth)
  return _driver


def query(cypher: str, params: dict | None = None, *, database: str) -> list:
  """Execute a Cypher query and return all records."""
  return get_driver().execute_query(cypher, params or {}, database_=database).records


def run(cypher: str, params: dict | None = None, *, database: str) -> None:
  """Execute a Cypher statement where the return value is not needed."""
  get_driver().execute_query(cypher, params or {}, database_=database)
