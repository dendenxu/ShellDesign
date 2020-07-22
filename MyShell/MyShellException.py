class MyShellException(Exception):
    """
    raised when we cannot find a particular key
    or duplication occurs
    """

    def __init__(self, message, errors=None):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.errors = errors


class MultipleInputException(MyShellException):
    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class ExitException(MyShellException):
    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class EmptyException(MyShellException):
    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class FileNotFoundException(MyShellException):
    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class QuoteUnmatchedException(MyShellException):
    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class SetPairUnmatchedException(MyShellException):
    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class CalledProcessException(MyShellException):
    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class ReservedKeyException(MyShellException):
    def __init__(self, message, errors=None):
        super().__init__(message, errors)

class UnsetKeyException(MyShellException):
    def __init__(self, message, errors=None):
        super().__init__(message, errors)