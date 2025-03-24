class FailedAfterRetriesException(Exception):
    """
    Exception raised when a process fails after a number of retries.
    """

    def __init__(self, message: str = "Failed after retries."):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"FailedAfterRetriesException: {self.message}"