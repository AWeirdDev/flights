from typing import Optional

from .airflights import Tfs, generate_trail

__all__ = ["url_from_tfs"]


def url_from_tfs(tfs: Tfs, *, trail: Optional[str] = None) -> str:
    """Gets flights page URL from Tfs.

    Example:

    .. code-block:: python

        tfs, res = get(..., verbose=True)
        print(url_from_tfs(tfs))

    Args:
        tfs (Tfs): Tfs data (param).
        trail (str, optional): Trailing random characters, if any.
    """
    try:
        from urllib.parse import quote
    except ModuleNotFoundError as err:
        raise ModuleNotFoundError(
            "Install `urllib3` (urllib) in order to use this utility function."
        ) from err

    return (
        "https://www.google.com/travel/flights/search?tfs="
        + quote(tfs.base64())
        + "_" * 12
        + (trail or generate_trail())
    )
