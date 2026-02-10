import contextvars
import logging
from typing import Optional

from taxos import DATA_DIR
from taxos.bucket.entity import Bucket, BucketRef
from taxos.bucket.load.query import LoadBucket
from taxos.context.entity import Context
from taxos.receipt.entity import Receipt, ReceiptRef
from taxos.receipt.load.query import LoadReceipt
from taxos.tenant.entity import Tenant, TenantRef
from taxos.tools import json

logger = logging.getLogger(__name__)

# Context variables for request-scoped data
_context_var: contextvars.ContextVar[Optional[Context]] = contextvars.ContextVar("context", default=None)


def get_default_context() -> Context:
  """For CLI tools."""
  context = Context(tenant=None)

  context_file = DATA_DIR / "default_context.json"
  logger.debug(f"Loading default context from {context_file}")
  if context_file.exists():
    data = json.loads(context_file.read_text())
    tenant = TenantRef(data["tenant"]).hydrate()
    context.tenant = tenant

  return context


def set_context(context: Context) -> None:
  """Set the current request context."""
  logger.debug(f"Setting context: {context}")
  _context_var.set(context)


def get_context() -> Optional[Context]:
  """Get the current request context, falling back to default context for CLI tools."""
  context = _context_var.get()
  if context is not None:
    return context

  return get_default_context()


def require_context() -> Context:
  """Get the current context, raising an error if none is set."""
  context = get_context()
  if context is None:
    raise RuntimeError("No context is currently set. Make sure to call set_context() first.")
  return context


def require_tenant(tenant: Tenant | TenantRef | None = None) -> Tenant:
  """Get the current tenant, raising an error if none is set."""
  if tenant:
    return tenant.hydrate()
  context = require_context()
  if tenant := context.tenant:
    return tenant
  raise RuntimeError("No tenant is available in the current context.")


def clear_context() -> None:
  """Clear the current context."""
  _context_var.set(None)


def with_context(context: Context):
  """Decorator to set context for a function call."""

  def decorator(func):
    def wrapper(*args, **kwargs):
      # Save the current context
      old_context = get_context()
      try:
        # Set the new context
        set_context(context)
        return func(*args, **kwargs)
      finally:
        # Restore the previous context
        if old_context is not None:
          set_context(old_context)
        else:
          clear_context()

    return wrapper

  return decorator


def require_bucket(value) -> Bucket:
  if isinstance(value, Bucket):
    return value
  elif not isinstance(value, BucketRef):
    value = BucketRef(value)
  return LoadBucket(value).execute()


def require_receipt(value) -> Receipt:
  """Hydrates a ReceiptRef to a Receipt, or returns the Receipt if already hydrated.
  Raises Receipt.DoesNotExist."""
  if isinstance(value, Receipt):
    return value
  elif not isinstance(value, ReceiptRef):
    value = ReceiptRef(value)
  return LoadReceipt(value).execute()
