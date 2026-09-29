class BaseException(Exception):
    message: str = "Internal Server Error"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.message)
        if message:
            self.message = message


class NotFoundException(BaseException):
    message = "Not Found"


class CreateException(BaseException):
    message = "Unable to create product"
