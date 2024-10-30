"""Custom Exceptions to be used with SSoT integrations."""


class JobException(Exception):
    """Exception raised when failure loading integration Job."""

    def __init__(self, message):
        """Populate exception information."""
        self.message = message
        super().__init__(self.message)
