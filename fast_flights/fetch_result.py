from dataclasses import dataclass, field


@dataclass
class FetchResult:
    """Result returned by integrations that can capture both HTML and XHR data."""

    html: str = ""
    xhr_bodies: list[str | bytes] = field(default_factory=list)
    url: str | None = None
