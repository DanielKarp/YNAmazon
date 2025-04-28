# YNAmazon
A program to annotate YNAB transactions with Amazon order info

## Setup/Prerequisites
1. **YNAB and Amazon Accounts**: Ensure you have active accounts for both YNAB and Amazon.
2. **Create a Renaming Rule in YNAB**:
   - In YNAB, go to the "Manage Payees" menu.
   - Create a rule to automatically rename any transactions containing "Amazon" to the payee name you want to use to indicate that the transaction needs to be processed. The default is `"Amazon - Needs Memo"`.
3. **Create a Processed Payee in YNAB**:
   - Create a payee in YNAB to indicate that a transaction has already been processed. For example, `"Amazon"`.
4. **Install Toolkit for YNAB (Optional)**:
   - Install the [Toolkit for YNAB](https://toolkitforynab.com/) browser extension.
   - Enable the following features for the best experience:
     - "Enable Markdown in Memos"
     - "Hyperlinks in the memo field"
5. **Set Up Environment Variables**:
   - Create a `.env` file to securely store your credentials and configuration:
     1. Make a copy of `.env-template` and rename it to `.env`.
     2. Add the following variables to the `.env` file:
        ```plaintext
        YNAB_API_KEY=your-ynab-api-key
        YNAB_BUDGET_ID=your-budget-id
        YNAB_PAYEE_NAME_TO_BE_PROCESSED="Amazon - Needs Memo"
        YNAB_PAYEE_NAME_PROCESSING_COMPLETED=Amazon
        YNAB_USE_MARKDOWN=true/false
        YNAB_USE_AI_SUMMARIZATION=true/false
        OPENAI_API_KEY=your-openai-api-key
        AMAZON_USER=your-amazon-email
        AMAZON_PASSWORD=your-amazon-password
        ```
6. **Install Dependencies**:
   - Install `uv` ([instructions](https://github.com/astral-sh/uv?tab=readme-ov-file#installation)) if needed
   - Run one of the following commands to install the required dependencies:
     ```bash
     # Basic installation (without AI features)
     uv sync

     # Installation with AI features
     uv sync --extra ai
     ```

## Use CLI

[CLI Instructions](/CLI_README.md)

## How it works
This program automates the process of annotating YNAB transactions with detailed Amazon order information. Here's how it works:

1. **Amazon Transactions Retrieval**: The program logs into your Amazon account using the `amazon-orders` library and retrieves your recent order history and transactions. It matches transactions with corresponding orders based on order numbers.

2. **YNAB Transactions Retrieval**: It connects to your YNAB account via the YNAB API and identifies transactions with a specific payee name (e.g., "Amazon - Needs Memo") that require annotation.

3. **Transaction Matching**: The program compares YNAB transactions with Amazon transactions by matching amounts to find corresponding orders.

4. **Memo Annotation**: For each matched transaction, it generates a detailed memo that includes:
   - A note if the transaction does not represent the full order total.
   - A list of items in the order.
   - A link to the Amazon order details.
   - If AI summarization is enabled, it will use OpenAI to generate a concise summary of the order.

5. **Transaction Update**: The program updates the YNAB transaction with the generated memo and changes its payee to a designated name (e.g., "Amazon") to mark it as processed.

6. **Automation**: This process is fully automated, reducing manual effort and ensuring accurate reconciliation of Amazon purchases in your YNAB budget.

The script relies on the `amazon-orders` library for Amazon data and the YNAB API for transaction updates.

There is an important distinction between an Amazon order and an Amazon transaction. When you check out, that is a single order. Often, one order will be fulfilled together, creating a single transaction. However, some orders will generate more than one transaction, which will show up in YNAB separately. This program handles this by adding the same memo to each transaction of that order, which includes a note that the transaction doesn't reflect the entire order.

### Sample Memo Format

For a transaction for an order with a single item, the memo format is as minimal as possible, for example:
``` plaintext
60 Gallon Barrel of Maple Syrup
https://www.amazon.com/gp/css/summary/edit.html?orderID=123-1234567-7654321
```

For orders with more than one item, they are listed in a numbered markdown list:
``` plaintext
1. Dog Costume
2. Facepaint
3. Popcorn-shaped Purse
https://www.amazon.com/gp/css/summary/edit.html?orderID=321-7890123-4567890
```

If AI summarization is enabled, the memo will be a concise summary of the order:
``` plaintext
Dog Costume, Facepaint, and Popcorn-shaped Purse
https://www.amazon.com/gp/css/summary/edit.html?orderID=321-7890123-4567890
```

If Amazon splits the order into multiple transactions, this program will detect that and warn you in the memo. In this case, YNAB will label all transactions for that order with the same memo. Unfortunately, it is not possible to easily tell which items belong to what transactions, so you may have to click on the link and figure it out for yourself:
``` plaintext
-This transaction doesn't represent the entire order. The order total is $99.99-

1. Dog Costume
2. Facepaint
3. Popcorn-shaped Purse
https://www.amazon.com/gp/css/summary/edit.html?orderID=321-7890123-4567890
```

## AI Summarization
The program can use OpenAI's GPT model to generate concise summaries of your Amazon orders. To enable this feature:

1. Install the package with AI features:
   ```bash
   uv sync --extra ai
   ```
2. Set `YNAB_USE_AI_SUMMARIZATION=true` in your `.env` file
3. Add your OpenAI API key: `OPENAI_API_KEY=your-openai-api-key`

When enabled, the program will:
- Generate concise summaries of orders with multiple items
- Preserve important information like order URLs and partial order warnings
- Fall back to standard truncation if AI summarization fails or is unavailable
- Will not use markdown formatting if enabled since this only increases memo length

## Limitations
This script probably won't be able to handle weird edge cases. The amazon-orders library is only able to handle amazon.com and will not pull data from other countries' amazon sites. Any transactions in the amazon transaction history that don't relate to an amazon.com order will be ignored. As with any tool that relies on web scraping, things can change at any time and it is up to the maintainers of the amazon-orders library to fix things.

## Disclaimer
This script requires your Amazon and YNAB credentials. Use at your own risk and ensure you store your credentials securely. The author is not responsible for any misuse or data breaches.
