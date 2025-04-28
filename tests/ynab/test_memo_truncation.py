# pyright: reportAttributeAccessIssue=false
"""Test script for memo truncation and summarization.

This module contains tests for the memo processing functionality, including:
- Truncation of long memos
- AI summarization of memos
- Handling of markdown formatting
- Proper preservation of order URLs and partial order warnings
"""

from collections.abc import Callable
from typing import Union
from unittest.mock import MagicMock, Mock, patch

import pytest
from faker import Faker
from openai import APIError, AuthenticationError
from pydantic import SecretStr

from ynamazon.settings import SecretApiKey, SecretBudgetId, Settings
from ynamazon.ynab_memo import (
    YNAB_MEMO_LIMIT,
    InvalidOpenAIAPIKey,
    OpenAIEmptyResponseError,
    extract_order_url,
    generate_ai_summary,
    normalize_memo,
    process_memo,
    truncate_memo,
)
from ynamazon.ynab_transactions import MemoField, simple_memo_truncate

fake = Faker()


# Test data
PARTIAL_ORDER_WARNING = (
    "-This transaction doesn't represent the entire order. The order total is $603.41-"
)
ORDER_URL_PLAIN = (
    "https://www.amazon.com/gp/your-account/order-details?orderID=113-2607970-8010001"
)
ORDER_URL_MARKDOWN = "[Order #113-2607960-6193002](https://www.amazon.com/gp/your-account/order-details?orderID=113-2607960-6193002)"


@pytest.fixture
def mock_settings() -> Settings:
    settings = MagicMock(spec=Settings)
    settings.ynab_api_key = SecretApiKey("fake_api_key")
    settings.ynab_budget_id = SecretBudgetId("fake_budget_id")
    settings.amazon_user = fake.email()
    settings.amazon_password = SecretStr("fake_password")
    settings.openai_api_key = SecretApiKey("fake_openai_key")

    return settings


@pytest.fixture
def test_memo_plain():
    """Fixture providing a plain text test memo."""
    return f"""
{PARTIAL_ORDER_WARNING}
**Items**
1. AIRMEGA Max 2 Air Purifier Replacement Filter Set for 300/300S
2. COWAY AP-1512HH & 200M Air Purifier Filter Replacement, Fresh Starter Pack, 2 Fresh Starter
Deodorization Filters and 1 True HEPA Filter, 1 Pack, Black
3. Chemical Guys ACC138 Secondary Container Dilution Bottle with Heavy Duty Sprayer, 16 oz, 3
Pack
4. Coway Airmega 150 Air Purifier Replacement Filter Set, Green True HEPA and Active Carbon
Filter, AP-1019C-FP
5. Coway Airmega 230/240 Air Purifier Replacement Filter Set, Max 2 Green True HEPA and Active
Carbon Filter
6. Nakee Butter Focus Nut Butter: High-Protein, Low-Carb Keto Peanut Butter with Cacao & MCT
Oil, 12g Protein - On-The-Go, 6 Packs.
7. ScanSnap iX1600 Wireless or USB High-Speed Cloud Enabled Document, Photo & Receipt Scanner
with Large Touchscreen and Auto Document Feeder for Mac or PC, 17 watts, Black
{ORDER_URL_PLAIN}
"""


@pytest.fixture
def test_memo_markdown():
    """Fixture providing a markdown-formatted test memo."""
    return f"""
{PARTIAL_ORDER_WARNING}

**Items**
1. [AIRMEGA Max 2 Air Purifier Replacement Filter Set for
300/300S](https://www.amazon.com/dp/B01C9RIAEE?ref=ppx_yo2ov_dt_b_fed_asin_title)
2. [COWAY AP-1512HH & 200M Air Purifier Filter Replacement, Fresh Starter Pack, 2 Fresh Starter
Deodorization Filters and 1 True HEPA Filter, 1 Pack,
Black](https://www.amazon.com/dp/B00C7WMQTW?ref=ppx_yo2ov_dt_b_fed_asin_title)
3. [Chemical Guys ACC138 Secondary Container Dilution Bottle with Heavy Duty Sprayer, 16 oz, 3
Pack](https://www.amazon.com/dp/B06WVJG4H8?ref=ppx_yo2ov_dt_b_fed_asin_title)
4. [Coway Airmega 150 Air Purifier Replacement Filter Set, Green True HEPA and Active Carbon
Filter, AP-1019C-FP](https://www.amazon.com/dp/B08JPCDVK8?ref=ppx_yo2ov_dt_b_fed_asin_title)
5. [Coway Airmega 230/240 Air Purifier Replacement Filter Set, Max 2 Green True HEPA and Active
Carbon Filter](https://www.amazon.com/dp/B0B9WX6L97?ref=ppx_yo2ov_dt_b_fed_asin_title)
6. [Nakee Butter Focus Nut Butter: High-Protein, Low-Carb Keto Peanut Butter with Cacao & MCT
Oil, 12g Protein - On-The-Go, 6
Packs.](https://www.amazon.com/dp/B072FGTT8P?ref=ppx_yo2ov_dt_b_fed_asin_title)
7. [ScanSnap iX1600 Wireless or USB High-Speed Cloud Enabled Document, Photo & Receipt Scanner
with Large Touchscreen and Auto Document Feeder for Mac or PC, 17 watts,
Black](https://www.amazon.com/dp/B08PH5Q51P?ref=ppx_yo2ov_dt_b_fed_asin_title)
{ORDER_URL_MARKDOWN}
"""


def test_truncation_preserves_important_elements(monkeypatch, test_memo_plain):
    """Test that truncation preserves warning and URL while staying under limit."""
    monkeypatch.setenv("USE_AI_SUMMARIZATION", "False")
    monkeypatch.setenv("YNAB_USE_MARKDOWN", "False")

    result = process_memo(test_memo_plain)

    # Check important elements are preserved
    assert PARTIAL_ORDER_WARNING in result
    assert ORDER_URL_PLAIN in result

    # Check structure
    lines = result.split("\n")
    assert "Items" in lines[1]
    assert any(line.startswith(str(i)) for i, line in enumerate(lines[2:-1], 1))


def test_truncation_with_markdown(monkeypatch, test_memo_markdown):
    """Test that truncation works correctly with markdown formatting."""
    monkeypatch.setenv("USE_AI_SUMMARIZATION", "False")
    monkeypatch.setenv("YNAB_USE_MARKDOWN", "True")

    result = process_memo(test_memo_markdown)

    # Check important elements are preserved
    assert PARTIAL_ORDER_WARNING in result
    assert ORDER_URL_MARKDOWN.split("]")[1].strip("()") in result


@patch("ynamazon.ynab_memo.generate_ai_summary")
def test_ai_summarization_plain(
    mock_generate_summary: Callable[..., Union[str, None]],
    monkeypatch,
    test_memo_plain,
):
    """Test AI summarization with plain text."""
    monkeypatch.setenv("USE_AI_SUMMARIZATION", "True")
    monkeypatch.setenv("YNAB_USE_MARKDOWN", "False")
    monkeypatch.setenv("OPENAI_API_KEY", fake.password(length=16))

    # Mock AI response
    mock_generate_summary.return_value = (
        "AIRMEGA Filter Set, COWAY Filters (2), Chemical Guys Bottles (3), More Items\n"
        + ORDER_URL_PLAIN
    )

    result = process_memo(test_memo_plain)

    # Check length
    assert len(result) <= YNAB_MEMO_LIMIT

    # Verify AI was called with correct parameters
    mock_generate_summary.assert_called_once()
    assert ORDER_URL_PLAIN in result


@patch("ynamazon.ynab_memo.generate_ai_summary")
def test_ai_summarization_markdown(
    mock_generate_summary, test_memo_markdown, monkeypatch
):
    """Test AI summarization with markdown formatting."""
    monkeypatch.setenv("USE_AI_SUMMARIZATION", "True")
    monkeypatch.setenv("YNAB_USE_MARKDOWN", "True")
    monkeypatch.setenv("OPENAI_API_KEY", fake.password(length=16))

    # Mock AI response
    mock_generate_summary.return_value = (
        "1. AIRMEGA Filter Set\n2. COWAY Filters (2)\n3. Chemical Guys Bottles (3)\n"
        + ORDER_URL_MARKDOWN
    )

    result = process_memo(test_memo_markdown)

    # Check length
    assert len(result) <= YNAB_MEMO_LIMIT

    # Verify AI was called with correct parameters
    mock_generate_summary.assert_called_once()
    assert ORDER_URL_MARKDOWN.split("]")[1].strip("()") in result


@pytest.mark.skip(
    reason="Settings class validates that OpenAI key is set when AI is used"
)
@patch("ynamazon.ynab_memo.generate_ai_summary")
def test_no_openai_key_falls_back_to_truncation(
    mock_generate_summary, test_memo_plain, monkeypatch
):
    """Test that process_memo falls back to truncation when no OpenAI key is available."""
    monkeypatch.setenv("USE_AI_SUMMARIZATION", "True")
    monkeypatch.delenv("OPEN_API_KEY", raising=False)
    mock_generate_summary.return_value = None

    result = process_memo(test_memo_plain)

    # Check that important elements are preserved
    assert PARTIAL_ORDER_WARNING in result
    assert ORDER_URL_PLAIN in result
    mock_generate_summary.assert_called_once()


def test_memo_under_limit_returns_unchanged(mock_settings):
    """Test that memos under the character limit are returned unchanged."""
    short_memo = "Short memo with URL\nhttps://amazon.com/orders/123"
    mock_settings.use_ai_summarization = False

    result = process_memo(short_memo)

    assert result == short_memo


def test_normalize_memo():
    """Test that normalize_memo correctly joins split URL lines."""
    # Test with hyphen-split URL
    memo = "Item 1\nhttps://www.amazon.com/gp/your-account/order-details?orderID=123-4567890-1234567\nItem 2"
    result = normalize_memo(memo)
    assert "Item 1" in result
    assert (
        "https://www.amazon.com/gp/your-account/order-details?orderID=123-4567890-1234567"
        in result
    )
    assert "Item 2" in result


def test_extract_order_url():
    """Test that extract_order_url correctly identifies URLs in different formats."""
    # Test plain URL
    memo = "Order details: https://www.amazon.com/gp/your-account/order-details?orderID=123-4567890-1234567"
    assert (
        extract_order_url(memo)
        == "https://www.amazon.com/gp/your-account/order-details?orderID=123-4567890-1234567"
    )

    # Test markdown URL
    memo = "Order details: [Order #123-4567890-1234567](https://www.amazon.com/gp/your-account/order-details?orderID=123-4567890-1234567)"
    assert (
        extract_order_url(memo)
        == "https://www.amazon.com/gp/your-account/order-details?orderID=123-4567890-1234567"
    )

    # Test no URL
    memo = "No URL here"
    assert extract_order_url(memo) is None


AUTH_ERROR = AuthenticationError(
    message="Invalid API key",
    response=Mock(status_code=401),
    body={"error": {"message": "Invalid API key"}},
)
API_ERROR = APIError(
    message="Internal server error",
    request=Mock(),
    body={"error": {"message": "Internal server error"}},
)


@pytest.fixture
def openai_api_key():
    return fake.password(length=16)


@pytest.fixture
def mock_ai_response():
    """Mock OpenAI API response."""
    mock_response = Mock()
    mock_response.choices = []
    return mock_response


def test_empty_ai_response_error_handling(
    mock_ai_response, monkeypatch, openai_api_key
):
    """Test handling of empty AI response."""
    monkeypatch.setenv("OPENAI_API_KEY", openai_api_key)

    with patch("ynamazon.ynab_memo.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_ai_response
        mock_openai.return_value = mock_client

        with pytest.raises(OpenAIEmptyResponseError):
            generate_ai_summary(["Item 1"], "not-a-url")


@pytest.mark.parametrize(
    ("fake_url", "side_effect", "expected_exception"),
    [
        ("https://amazon.com/order/123", AUTH_ERROR, InvalidOpenAIAPIKey),
        ("not-a-url", API_ERROR, None),
    ],
)
def test_generate_ai_summary_error_handling(
    fake_url: str,
    side_effect: APIError,
    expected_exception,
    monkeypatch,
    openai_api_key,
):
    """Test error handling in generate_ai_summary."""
    monkeypatch.setenv("OPENAI_API_KEY", openai_api_key)

    # Test with invalid API key
    with (
        patch("ynamazon.ynab_memo.OpenAI") as mock_openai,
    ):
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = side_effect
        mock_openai.return_value = mock_client

        if expected_exception is None:
            result = generate_ai_summary(["Item 1"], fake_url)
            assert result is None
        else:
            with pytest.raises(expected_exception):
                generate_ai_summary(["Item 1"], fake_url)


def test_partial_order_warning_variations(test_memo_plain, monkeypatch):
    """Test handling of different partial order warning formats."""
    monkeypatch.setenv("USE_AI_SUMMARIZATION", "False")

    # Test with different amounts
    variations = [
        "-This transaction doesn't represent the entire order. The order total is $1.23-",
        "-This transaction doesn't represent the entire order. The order total is $1,234.56-",
        "-This transaction doesn't represent the entire order. The order total is $1,234,567.89-",
    ]

    for warning in variations:
        memo = warning + "\n" + test_memo_plain.split("\n", 1)[1]
        result = process_memo(memo)
        assert warning in result
        assert ORDER_URL_PLAIN in result


def test_truncate_memo_character_limit():
    """Test character limit calculations in truncate_memo."""
    # Create a memo that's exactly at the limit
    items = ["Item " + str(i) for i in range(10)]
    url = "https://amazon.com/order/123"
    memo = "\n".join(items) + "\n" + url

    # Should be unchanged
    result = truncate_memo(memo)
    assert result == memo

    # Add one character to exceed limit
    memo = memo + "x"
    result = truncate_memo(memo)
    assert len(result) <= YNAB_MEMO_LIMIT
    assert url in result


def test_malformed_markdown_handling(monkeypatch):
    """Test handling of malformed markdown and URLs."""
    monkeypatch.setenv("USE_AI_SUMMARIZATION", "False")
    monkeypatch.setenv("YNAB_USE_MARKDOWN", "False")

    # Test with unclosed markdown link
    memo = "Unclosed link\nhttps://amazon.com/order/123"
    result = process_memo(memo)
    assert "Unclosed link" in result
    assert "https://amazon.com/order/123" in result

    # Test with malformed URL
    memo = "Order #123 (not-a-url)"
    result = process_memo(memo)
    assert "Order #123" in result


@pytest.mark.skip(reason="Function needs more work")
def test_simple_memo_truncate():
    memo_field = MemoField(
        header_lines=[PARTIAL_ORDER_WARNING],
        item_lines=[
            (
                1,
                "[AIRMEGA Max 2 Air Purifier Replacement Filter Set for 300/300S](https://www.amazon.com/dp/B01C9RIAEE?ref=ppx_yo2ov_dt_b_fed_asin_title)",
            ),
            (
                2,
                "[COWAY AP-1512HH & 200M Air Purifier Filter Replacement, Fresh Starter Pack, 2 Fresh Starter Deodorization Filters and 1 True HEPA Filter, 1 Pack, Black](https://www.amazon.com/dp/B00C7WMQTW?ref=ppx_yo2ov_dt_b_fed_asin_title)",
            ),
            (
                3,
                "[Chemical Guys ACC138 Secondary Container Dilution Bottle with Heavy Duty Sprayer, 16 oz, 3 Pack](https://www.amazon.com/dp/B06WVJG4H8?ref=ppx_yo2ov_dt_b_fed_asin_title)",
            ),
            (
                4,
                "[Coway Airmega 150 Air Purifier Replacement Filter Set, Green True HEPA and Active Carbon Filter, AP-1019C-FP](https://www.amazon.com/dp/B08JPCDVK8?ref=ppx_yo2ov_dt_b_fed_asin_title)",
            ),
            (
                5,
                "[Coway Airmega 230/240 Air Purifier Replacement Filter Set, Max 2 Green True HEPA and Active Carbon Filter](https://www.amazon.com/dp/B0B9WX6L97?ref=ppx_yo2ov_dt_b_fed_asin_title)",
            ),
            (
                6,
                "[Nakee Butter Focus Nut Butter: High-Protein, Low-Carb Keto Peanut Butter with Cacao & MCT Oil, 12g Protein - On-The-Go, 6 Packs.](https://www.amazon.com/dp/B072FGTT8P?ref=ppx_yo2ov_dt_b_fed_asin_title)",
            ),
            (
                7,
                "[ScanSnap iX1600 Wireless or USB High-Speed Cloud Enabled Document, Photo & Receipt Scanner with Large Touchscreen and Auto Document Feeder for Mac or PC, 17 watts, Black](https://www.amazon.com/dp/B08PH5Q51P?ref=ppx_yo2ov_dt_b_fed_asin_title)",
            ),
        ],
        footer_lines=[ORDER_URL_MARKDOWN],
    )

    assert len(memo_field) >= YNAB_MEMO_LIMIT, "Memo is shorter than expected"

    truncated, memo_text = simple_memo_truncate(memo_field)
    assert len(memo_text) <= YNAB_MEMO_LIMIT, "Truncated memo exceeds YNAB limit"
    assert truncated, "Memo was not truncated"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
