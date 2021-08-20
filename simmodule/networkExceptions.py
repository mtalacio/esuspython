
class InvalidResponseException (Exception):
    def __init__(self, message):
        self.message = message

class GPSNotFixedException (Exception):
    def __init__(self, message):
        self.message = message

class SIMNetworkError (Exception):
    def __init__(self, message):
        self.message = message