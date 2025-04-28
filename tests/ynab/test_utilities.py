# pyright: reportAttributeAccessIssue=false


from ynamazon.ynab_transactions import markdown_formatted_link, markdown_formatted_title


def test_default_settings_env():
    """Just a sanity check to ensure that the environment is setup properly from conftest.py."""
    import os

    assert os.getenv("YNAB_API_KEY") is not None, "YNAB_API_KEY is not set"


def test_markdown_formatted_link_use_markdown(monkeypatch):
    monkeypatch.setenv("YNAB_USE_MARKDOWN", "True")

    title = "Test Title"
    url = "https://example.com"
    expected_result = f"[{title}]({url})"

    assert markdown_formatted_link(title, url) == expected_result


def test_markdown_formatted_link_no_markdown(monkeypatch):
    monkeypatch.setenv("YNAB_USE_MARKDOWN", "False")

    title = "Test Title"
    url = "https://example.com"
    expected_result = url

    assert markdown_formatted_link(title, url) == expected_result


def test_markdown_formatted_title_use_markdown(monkeypatch):
    monkeypatch.setenv("YNAB_USE_MARKDOWN", "True")

    title = "Test Title"
    url = "https://example.com"
    expected_result = f"[{title}]({url})"

    assert markdown_formatted_title(title, url) == expected_result


def test_markdown_formatted_title_no_markdown(monkeypatch):
    monkeypatch.setenv("YNAB_USE_MARKDOWN", "False")

    title = "Test Title"
    url = "https://example.com"
    expected_result = title

    assert markdown_formatted_title(title, url) == expected_result
