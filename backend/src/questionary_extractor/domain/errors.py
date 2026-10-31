class QuestionnaireError(Exception):
    pass


class UnsupportedFileError(QuestionnaireError):
    pass


class FileTooLargeError(QuestionnaireError):
    pass


class NoItemsDetectedError(QuestionnaireError):
    pass


class ExtractionError(QuestionnaireError):
    pass


class LLMUnavailableError(QuestionnaireError):
    pass


class LLMTimeoutError(QuestionnaireError):
    def __init__(
        self,
        message: str = "The document took too long to process. Try a smaller file.",
    ):
        super().__init__(message)


class DocumentTooLongError(QuestionnaireError):
    def __init__(
        self,
        message: str = "The document is too long to process. Try a shorter file.",
    ):
        super().__init__(message)


class ProcessingError(QuestionnaireError):
    def __init__(
        self,
        message: str = "Something went wrong while processing the file. Please try again.",
    ):
        super().__init__(message)
