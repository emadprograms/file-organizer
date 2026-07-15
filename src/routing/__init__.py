import logging
from .router import route_document, RoutingResponse

logger = logging.getLogger(f"file_organizer.{__name__}")

__all__ = ["route_document", "RoutingResponse"]
