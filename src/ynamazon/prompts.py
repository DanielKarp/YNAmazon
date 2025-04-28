"""AI prompt templates for generating summaries of Amazon orders.

This file contains customizable prompt templates used by the AI summarization functionality.
"""

# System prompt defines the AI assistant's behavior
AMAZON_SUMMARY_SYSTEM_PROMPT = """
You are a helpful assistant that summarizes Amazon orders for YNAB memos.
Your goal is to create concise, readable summaries that fit within YNAB's 500 character limit.
Focus on preserving important information like order URLs and partial order warnings.

Rules:
- Omit all Amazon branding (don't include "Amazon", "Amazon Basics", "Amazon Essentials", etc.)
- Keep descriptions under 50 characters whenever possible
- Focus on the essential details of what the item is
- Remove brands when possible unless it's a notable brand
- Preserve the original casing of all words
- Omit quantity information when the quantity is 1 (don't include '(1)' in the description)
- If quantity is greater than 1, include it in parentheses like "(3)"
- Do not use sentence case or title case - keep the casing exactly as provided in the input
"""

# User prompt for non-markdown (plain text) format
AMAZON_SUMMARY_PLAIN_PROMPT = """
Please provide a concise summary of this Amazon order.

For a single item order, just list the item name by itself with no prefix. If a quantity is mentioned and greater than 1, put it in parentheses at the end.
For example: "Barrel of Maple Syrup" or "Protein Bars (12)"

For multiple items, list them with a comma-separated format, with quantities in parentheses at the end of each item:
For example: "Dog Costume, Facepaint (2), Popcorn-shaped Purse"

Do not include the order URL or any additional information - just the item list.
"""

# User prompt for markdown-formatted list with numbered items
AMAZON_SUMMARY_MARKDOWN_PROMPT = """
Please provide a concise summary of this Amazon order as a markdown-formatted numbered list.

For a single item order, just list the item name by itself with no numbering. If a quantity is mentioned and greater than 1, put it in parentheses at the end.
For example: "Barrel of Maple Syrup" or "Protein Bars (12)"

For multiple items, number each item and put quantities in parentheses at the end of each item:
For example:
"1. Dog Costume
2. Facepaint (2)
3. Popcorn-shaped Purse"

Do not include the order URL or any additional information - just the item list.
"""
