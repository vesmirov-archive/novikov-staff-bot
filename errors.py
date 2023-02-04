

class InvalidConfigurationFileTypeError(BaseException):
    def __init__(self):
        self.message = 'The configuration file is either not in JSON format or invalid.'
        super().__init__()
