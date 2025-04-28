from functools import lru_cache
from os import PathLike
from pathlib import Path
from typing import Union

from pydantic import BaseModel, ConfigDict, EmailStr, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .exceptions import MissingOpenAIAPIKey


class SecretApiKey(SecretStr):
    """Secret API key."""

    def _display(self) -> str:
        """Masked secret API key."""
        if self._secret_value is None:
            return "****empty****"
        if len(self._secret_value) > 16:
            return self._secret_value[:4] + "****" + self._secret_value[-4:]
        if len(self._secret_value) > 8:
            return "******" + self._secret_value[-2:]
        return "********"


class SecretBudgetId(SecretStr):
    """Secret Budget ID."""

    def _display(self) -> str:
        """Masked secret Budget ID."""
        if self._secret_value is None:
            return "****empty****"
        return self._secret_value[:4] + "****" + self._secret_value[-4:]


class Settings(BaseSettings):
    """Settings configuration for project."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore",
    )

    ynab_api_key: SecretApiKey
    ynab_budget_id: SecretBudgetId
    amazon_user: EmailStr
    amazon_password: SecretStr
    openai_api_key: Union[SecretApiKey, None] = None

    ynab_payee_name_to_be_processed: str = "Amazon - Needs Memo"
    ynab_payee_name_processing_completed: str = "Amazon"
    ynab_use_markdown: bool = False
    use_ai_summarization: bool = False
    suppress_partial_order_warning: bool = False

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        """Validate that OpenAI API key is present when AI summarization is enabled."""
        if self.use_ai_summarization and self.openai_api_key is None:
            raise MissingOpenAIAPIKey(
                "OpenAI API key is required when AI summarization is enabled"
            )
        return self

    def get_secret_value(self, key: str) -> Union[str, None]:
        """Get secret API key or budget ID."""
        value = getattr(self, key)
        if value is None:
            return None
        if not isinstance(value, SecretStr):
            raise ValueError(f"{key} is not a SecretStr")
        return value.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    """Get settings from environment variables."""
    return Settings()  # type: ignore[call-arg]


class ConfigFile(BaseModel):
    """Configuration file for CLI."""

    model_config = ConfigDict(extra="forbid")
    ynab_api_key: Union[SecretApiKey, None] = None
    ynab_budget_id: Union[SecretBudgetId, None] = None
    amazon_user: Union[EmailStr, None] = None
    amazon_password: Union[SecretStr, None] = None

    ynab_payee_name_to_be_processed: Union[str, None] = None
    ynab_payee_name_processing_completed: Union[str, None] = None
    ynab_use_markdown: Union[bool, None] = None

    @classmethod
    def from_config(cls, file: Union[str, PathLike]):
        file_path = Path(file)
        if not file_path.exists():
            raise FileNotFoundError(f"Config file {file_path} does not exist.")
        if not file_path.is_file():
            raise ValueError(f"Config file {file_path} is not a file.")

        if file_path.suffix == ".yaml":
            return cls.model_validate_yaml(file_path.read_text())
        if file_path.suffix == ".toml":
            return cls.model_validate_toml(file_path.read_text())
        raise ValueError(f"Config file {file_path} must be a .toml or .yaml file.")

    @classmethod
    def model_validate_yaml(cls, yaml_str: str):
        """Validates a YAML string and returns a model instance."""
        import yaml

        data = yaml.safe_load(yaml_str)
        return cls.model_validate(data)

    @classmethod
    def model_validate_toml(cls, toml_str: str):
        """Validates a TOML string and returns a model instance."""
        import toml

        data = toml.loads(toml_str)
        return cls.model_validate(data)
