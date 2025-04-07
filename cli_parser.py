import argparse

class CLIParser:
    """Parses cli arguments using argparse, making them available outside. This class is a Singleton (only one instance)."""
    _instance = None

    def __new__(cls, *_args, **_kwargs):
        """This method implements the Singleton logic."""
        if cls._instance is None:
            cls._instance = super().__new__(cls, *_args, **_kwargs)

        return cls._instance

    def __init__(self):
        """Initialize by parsing the args."""
        self._args = self._parse_args()

    def __getattr__(self, name):
        """This method passes through methods directly to the underlying args that were argparsed."""
        return getattr(self._args, name)

    def _parse_args(self):
        """This method parses using argparse."""
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--force-refresh-amazon',
            help="Refreshes transactions directly from Amazon instead of using a recently cached version.",
            default=False,
            type=bool,
            action=argparse.BooleanOptionalAction
        )
        return parser.parse_args()
