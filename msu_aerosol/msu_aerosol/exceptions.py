__all__ = []


class TimeFormatError(Exception):
    def __init__(self, message):
        super().__init__(message)


class ColumnsMatchError(Exception):
    def __init__(self, message):
        super().__init__(message)


class CouldNotPreprocessDataError(Exception):
    def __init__(self, message):
        super().__init__(message)
