import pytest
from faker import Faker

from ynamazon.settings import get_settings

fake = Faker()

REQUIRED_ENV_VARS = {
    "YNAB_API_KEY": fake.password(length=16),
    "YNAB_BUDGET_ID": fake.password(length=16),
    "AMAZON_USER": fake.email(),
    "AMAZON_PASSWORD": fake.password(length=16),
}


@pytest.fixture(autouse=True)
def default_settings_env(monkeypatch):
    """Clear the settings cache before each test."""
    for key, value in REQUIRED_ENV_VARS.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()  # Clear the settings cache to ensure fresh values are used
