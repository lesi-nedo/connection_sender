

class NoSendButtonException(Exception):
    def __init__(self, message="No send button found"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}" 