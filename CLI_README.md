# `yna`

<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">Run &#x27;yna&#x27; to match and update transactions using the arguements in .env. </span>

<span style="color: #808000; text-decoration-color: #808000; font-style: italic">Use &#x27;yna ynamazon [ARGS]&#x27; to use command-line arguements to override .env. </span>

**Usage**:

```console
$ yna [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `print-ynab`: <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">Prints YNAB transactions.</span>
* `print-amazon`: <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">Prints Amazon transactions.</span>
* `ynamazon`: <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">Match YNAB transactions to...</span>
* `new-ynamazon`
* `utils`: <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">Utility commands</span>

## `yna print-ynab`

<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">Prints YNAB transactions.</span>

<span style="color: #808000; text-decoration-color: #808000; font-style: italic">All arguments will use defaults in .env file if not provided.</span>

**Usage**:

```console
$ yna print-ynab [OPTIONS] [API_KEY] [BUDGET_ID]
```

**Arguments**:

* `[API_KEY]`: YNAB API key  [default: (dynamic)]
* `[BUDGET_ID]`: YNAB Budget ID  [default: (dynamic)]

**Options**:

* `--help`: Show this message and exit.

## `yna print-amazon`

<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">Prints Amazon transactions.</span>

<span style="color: #808000; text-decoration-color: #808000; font-style: italic">All required arguments will use defaults in .env file if not provided.</span>

**Usage**:

```console
$ yna print-amazon [OPTIONS] [USER_EMAIL] [USER_PASSWORD]
```

**Arguments**:

* `[USER_EMAIL]`: Amazon username  [default: (dynamic)]
* `[USER_PASSWORD]`: Amazon password  [default: (dynamic)]

**Options**:

* `-y, --years INTEGER`: Order years; leave empty for current year
* `-d, --days INTEGER`: Days of transactions to retrieve  [default: 31]
* `--help`: Show this message and exit.

## `yna ynamazon`

<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">Match YNAB transactions to Amazon Transactions and optionally update YNAB Memos.</span>

<span style="color: #808000; text-decoration-color: #808000; font-style: italic">All required arguments will use defaults in .env file if not provided.</span>

**Usage**:

```console
$ yna ynamazon [OPTIONS] [YNAB_API_KEY] [YNAB_BUDGET_ID] [AMAZON_USER] [AMAZON_PASSWORD]
```

**Arguments**:

* `[YNAB_API_KEY]`: YNAB API key  [default: (dynamic)]
* `[YNAB_BUDGET_ID]`: YNAB Budget ID  [default: (dynamic)]
* `[AMAZON_USER]`: Amazon username  [default: (dynamic)]
* `[AMAZON_PASSWORD]`: Amazon password  [default: (dynamic)]

**Options**:

* `--help`: Show this message and exit.

## `yna new-ynamazon`

**Usage**:

```console
$ yna new-ynamazon [OPTIONS] [YNAB_API_KEY] [YNAB_BUDGET_ID] [AMAZON_USER] [AMAZON_PASSWORD]
```

**Arguments**:

* `[YNAB_API_KEY]`: YNAB API key
* `[YNAB_BUDGET_ID]`: YNAB Budget ID
* `[AMAZON_USER]`: Amazon username
* `[AMAZON_PASSWORD]`: Amazon password

**Options**:

* `-c, --config FILE`
* `--force-logout / --no-force-logout`: [default: no-force-logout]
* `-d, --debug`: Enable debug mode
* `--help`: Show this message and exit.

## `yna utils`

<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">Utility commands</span>

**Usage**:

```console
$ yna utils [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `check-amazon-orders`: Check the Amazon orders repository...

### `yna utils check-amazon-orders`

Check the Amazon orders repository integration test status.

**Usage**:

```console
$ yna utils check-amazon-orders [OPTIONS] [REPO_URL]
```

**Arguments**:

* `[REPO_URL]`: [default: (dynamic)]

**Options**:

* `-f, --filename TEXT`: Name of the workflow file to check.  [default: integration.yml]
* `--help`: Show this message and exit.
