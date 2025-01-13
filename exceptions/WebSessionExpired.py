

class WebSessionExpired(Exception):
    def __init__(self, message: str = None):
        self.message = message
        super().__init__(message)

    
    def __str__(self):
        return f"WebSessionExpired({self.message})"

    