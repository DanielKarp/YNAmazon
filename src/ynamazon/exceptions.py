class YnabSetupError(Exception):
    """Custom exception for YNAB setup errors."""

    pass


class MissingOpenAIAPIKey(Exception):
    """Raised when OpenAI API key is required but not found."""

    pass


class InvalidOpenAIAPIKey(Exception):
    """Raised when OpenAI API key is invalid or authentication fails."""

    pass


class OpenAIEmptyResponseError(Exception):
    """Raised when OpenAI returns an empty or invalid response."""

    pass
