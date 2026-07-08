import pytest
from src.core.exceptions import FileOrganizerError, ConfigurationError, ValidationError

def test_exception_hierarchy():
    """Verify that custom exceptions inherit from the base class."""
    with pytest.raises(ConfigurationError):
        raise ConfigurationError("Config error")
    
    with pytest.raises(FileOrganizerError):
        raise ConfigurationError("Config error")
        
    with pytest.raises(ValidationError):
        raise ValidationError("Validation error")
        
    with pytest.raises(FileOrganizerError):
        raise ValidationError("Validation error")

def test_exception_messages():
    """Verify that exception messages are preserved."""
    msg = "Critical configuration failure"
    with pytest.raises(ConfigurationError, match=msg):
        raise ConfigurationError(msg)
