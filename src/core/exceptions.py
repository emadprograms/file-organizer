import logging

logger = logging.getLogger(f"file_organizer.{__name__}")

class FileOrganizerError(Exception):
    """Base exception for all File Organizer errors."""
    pass

class PipelineHaltError(FileOrganizerError):
    """Raised when a critical error occurs that requires the entire pipeline to halt."""
    pass

class ConfigurationError(FileOrganizerError):

    """Raised when there is an issue with the configuration or environment."""
    pass

class ValidationError(FileOrganizerError):
    """Raised when a validation check fails."""
    pass

class ProviderRotationExhaustedError(FileOrganizerError):
    """Raised when all LLM providers in the rotation sequence have failed."""
    pass

class GracefulHaltException(FileOrganizerError):
    """Raised to signal a graceful halt of the process, allowing for state persistence."""
    pass
