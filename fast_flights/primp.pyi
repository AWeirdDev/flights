from typing import Any, Dict, Optional, Tuple

class Client:
    """Initializes an HTTP client that can impersonate web browsers.

    Args:
        auth (tuple, optional): A tuple containing the username and password for basic authentication. Default is None.
        auth_bearer (str, optional): Bearer token for authentication. Default is None.
        params (dict, optional): Default query parameters to include in all requests. Default is None.
        headers (dict, optional): Default headers to send with requests. If `impersonate` is set, this will be ignored.
        cookies (dict, optional): - An optional map of cookies to send with requests as the `Cookie` header.
        timeout (float, optional): HTTP request timeout in seconds. Default is 30.
        cookie_store (bool, optional): Enable a persistent cookie store. Received cookies will be preserved and included
            in additional requests. Default is True.
        referer (bool, optional): Enable or disable automatic setting of the `Referer` header. Default is True.
        proxy (str, optional): Proxy URL for HTTP requests. Example: "socks5://127.0.0.1:9150". Default is None.
        impersonate (str, optional): Entity to impersonate. Example: "chrome_124". Default is None.
            Chrome: "chrome_100","chrome_101","chrome_104","chrome_105","chrome_106","chrome_107","chrome_108",
                "chrome_109","chrome_114","chrome_116","chrome_117","chrome_118","chrome_119","chrome_120",
                "chrome_123","chrome_124","chrome_126","chrome_127","chrome_128"
            Safari: "safari_ios_16.5","safari_ios_17.2","safari_ios_17.4.1","safari_15.3","safari_15.5","safari_15.6.1",
                "safari_16","safari_16.5","safari_17.0","safari_17.2.1","safari_17.4.1","safari_17.5"
            OkHttp: "okhttp_3.9","okhttp_3.11","okhttp_3.13","okhttp_3.14","okhttp_4.9","okhttp_4.10","okhttp_5"
            Edge: "edge_101","edge_122","edge_127"
        follow_redirects (bool, optional): Whether to follow redirects. Default is True.
        max_redirects (int, optional): Maximum redirects to follow. Default 20. Applies if `follow_redirects` is True.
        verify (bool, optional): Verify SSL certificates. Default is True.
        ca_cert_file (str, optional): Path to CA certificate store. Default is None.
        http1 (bool, optional): Use only HTTP/1.1. Default is None.
        http2 (bool, optional): Use only HTTP/2. Default is None.

    """

    def __init__(
        self,
        auth: Optional[Tuple[str, Optional[str]]] = None,
        auth_bearer: Optional[str] = None,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = 30,
        cookie_store: Optional[bool] = True,
        referer: Optional[bool] = True,
        proxy: Optional[str] = None,
        impersonate: Optional[str] = None,
        follow_redirects: Optional[bool] = True,
        max_redirects: Optional[int] = 20,
        verify: Optional[bool] = True,
        ca_cert_file: Optional[str] = None,
        http1: Optional[bool] = None,
        http2: Optional[bool] = None,
    ): ...
    def get(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        auth: Optional[Tuple[str, Optional[str]]] = None,
        auth_bearer: Optional[str] = None,
        timeout: Optional[float] = 30,
    ) -> "Response":
        """Performs a GET request to the specified URL.

        Args:
            url (str): The URL to which the request will be made.
            params (Optional[Dict[str, str]]): A map of query parameters to append to the URL. Default is None.
            headers (Optional[Dict[str, str]]): A map of HTTP headers to send with the request. Default is None.
            cookies (Optional[Dict[str, str]]): - An optional map of cookies to send with requests as the `Cookie` header.
            auth (Optional[Tuple[str, Optional[str]]]): A tuple containing the username and an optional password
                for basic authentication. Default is None.
            auth_bearer (Optional[str]): A string representing the bearer token for bearer token authentication. Default is None.
            timeout (Optional[float]): The timeout for the request in seconds. Default is 30.

        """

    def post(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        content: Optional[bytes] = None,
        data: Optional[Dict[str, str]] = None,
        json: Any = None,
        files: Optional[Dict[str, bytes]] = None,
        auth: Optional[Tuple[str, Optional[str]]] = None,
        auth_bearer: Optional[str] = None,
        timeout: Optional[float] = 30,
    ):
        """Performs a POST request to the specified URL.

        Args:
            url (str): The URL to which the request will be made.
            params (Optional[Dict[str, str]]): A map of query parameters to append to the URL. Default is None.
            headers (Optional[Dict[str, str]]): A map of HTTP headers to send with the request. Default is None.
            cookies (Optional[Dict[str, str]]): - An optional map of cookies to send with requests as the `Cookie` header.
            content (Optional[bytes]): The content to send in the request body as bytes. Default is None.
            data (Optional[Dict[str, str]]): The form data to send in the request body. Default is None.
            json (Any): A JSON serializable object to send in the request body. Default is None.
            files (Optional[Dict[str, bytes]]): A map of file fields to file contents to be sent as multipart/form-data. Default is None.
            auth (Optional[Tuple[str, Optional[str]]]): A tuple containing the username and an optional password
                for basic authentication. Default is None.
            auth_bearer (Optional[str]): A string representing the bearer token for bearer token authentication. Default is None.
            timeout (Optional[float]): The timeout for the request in seconds. Default is 30.
        """

class Response:
    content: str
    cookies: Dict[str, str]
    headers: Dict[str, str]
    status_code: int
    text: str
    text_markdown: str
    text_plain: str
    text_rich: str
    url: str
