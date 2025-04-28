# Contributing to YNAmazon

Thank you for considering contributing to YNAmazon! To ensure a smooth contribution process, please follow the guidelines below.

### Visual Studio Code

#### Helpful Extensions
If using VSCode, install [Pylance](https://marketplace.visualstudio.com/items/?itemName=ms-python.vscode-pylance) and [Ruff](https://marketplace.visualstudio.com/items/?itemName=charliermarsh.ruff) extensions. This will add linting and type-checking directly into the editor.

## Easy Mode

### 1. Install with `uv`

Install package with all development and testing dependencies.
```bash
uv sync --all-groups --all-extras
uv run pre-commit install
```

We use [pre-commit](https://pre-commit.com/) to enforce code quality and formatting standards. Before committing your changes, ensure that all pre-commit checks pass.

Do __not__ skip installing pre-commit. This will enforce running the checks during all commits.

### 2. Pre-emptively Run Pre-Commit

#### Git will force it to run, but it will cause the entire commit to fail which can be frustrating. Running it manually first makes sure that it will pass during commit.

1. Stage all changes (`git add .`)
1. `uv run pre-commit run`

### 3. (Optional) Run [tox](https://tox.wiki/en/latest/index.html)

We use `tox` to test the project across multiple Python versions. While running `tox` locally is optional, it is highly recommended to catch issues early.

*Assumes that project was installed with all dependencies*

1. Run tox:
    ```bash
    uv run tox r

If only one environment is required to be run, use:

`uv run tox r -e py39` or `uv run tox r -e pre-commit`


### 4. GitHub Workflow for Tox
All pull requests are automatically tested using a GitHub Actions workflow that runs `tox`. Pull requests will not be considered if the workflow fails. Ensure that your changes pass all tests before submitting a pull request.

#### Submitting a Pull Request

1. Fork the repository and create a new branch for your feature or bugfix.
1. Make your changes and commit them with clear, descriptive messages. ([commitizen](https://commitizen-tools.github.io/commitizen/) is included to streamline this process)

    `uv run cz c`

Ensure that:
1. Pre-commit checks pass.
1. (Optional) Tox tests pass locally.
1. Push your branch and open a pull request.

Thank you for contributing!
