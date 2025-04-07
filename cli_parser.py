import argparse

class CLIParser:
    _instance = None

    def __new__(cls, *_args, **_kwargs):
        if cls._instance == None:
            cls._instance = super().__new__(cls, *_args, **_kwargs)

        return cls._instance

    def __init__(self):
        self.args = self._parse_args()

    def __getattr__(self, name):
        # import pdb; pdb.set_trace();
        return getattr(self.args, name)

    def _parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--force-refresh-amazon',
            help="Refreshes transactions directly from Amazon instead of using a recently cached version",
            default=False,
            type=bool,
            action=argparse.BooleanOptionalAction
        )
        return parser.parse_args()
