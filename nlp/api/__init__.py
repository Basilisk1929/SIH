"""NLP API subpackage."""

from nlp.api.service import app
from nlp.api.routes import router

__all__ = ["app", "router"]
