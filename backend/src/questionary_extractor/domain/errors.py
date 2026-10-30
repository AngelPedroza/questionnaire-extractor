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
