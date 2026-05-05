import os
from abc import ABC

from ..fetch_result import FetchResult
from ..querying import Query

try:
    import dotenv  # pip install python-dotenv

    dotenv.load_dotenv()

except ModuleNotFoundError:
    pass


class Integration(ABC):
    """Represents an integration."""

    def fetch_html(self, q: Query | str, /) -> str | FetchResult:
        """Fetch the flights page HTML from a query.

        Args:
            q: The query.
        """
        raise NotImplementedError


def get_env(k: str, /) -> str:
    """(utility) Get environment variable.

    If nothing found, raises an error.

    Returns:
        str: The value.
    """
    try:
        return os.environ[k]
    except KeyError:
        raise OSError(f"could not find environment variable: {k!r}")
