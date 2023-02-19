

class InvalidConfigurationFileTypeError(BaseException):
    def __init__(self):
        message = 'The configuration file is either not in JSON format or invalid.'
        super().__init__(message)


class InvalidGoogleServiceFileTypeError(BaseException):
    def __init__(self):
        message = 'The google service file is either not in JSON format or invalid.'
        super().__init__(message)
