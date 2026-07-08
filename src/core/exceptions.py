import logging

logger = logging.getLogger(f"file_organizer.{__name__}")

class FileOrganizerError(Exception):
    """Base exception for all File Organizer errors."""
    pass

class ConfigurationError(FileOrganizerError):
    """Raised when there is an issue with the configuration or environment."""
    pass

class ValidationError(FileOrganizerError):
    """Raised when a validation check fails."""
    pass
