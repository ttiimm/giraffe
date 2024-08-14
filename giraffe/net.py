import gzip
import socket
import ssl
import time
from dataclasses import dataclass, field
from enum import Enum
from io import BytesIO
from typing import IO, Mapping

"""An implementation of network code for fetching web pages.

This code is based on Chapter 1 of 
[Web Browser Engineering](https://browser.engineering/http.html).
"""

ABOUT_BLANK = "<html><head></head><body></body></html>"


@dataclass
class Response:
    version: str = ""
    status: str = ""
    explanation: str = ""
    # XXX: can this be a [str, List[str]]
    headers: Mapping[str, str] = field(default_factory=dict)
    body: str = ABOUT_BLANK


Scheme = Enum("Scheme", ["HTTP", "HTTPS", "FILE", "DATA", "ABOUT"])
DEFAULT_PORTS = {Scheme.HTTP: 80, Scheme.HTTPS: 443}

MAX_CHUNK = 16 * 1024


class URL(object):
    def __init__(self, url: str):
        self.is_viewsource = False
        if url.startswith("view-source:"):
            self.is_viewsource = True
            url = url.removeprefix("view-source:")

        scheme, url = url.split(":", 1)
        self.scheme = Scheme[scheme.upper()]
        url = url.lstrip("/")
        # XXX ewww
        if self.scheme in (Scheme.FILE, Scheme.DATA):
            url = f"/{url}"
        if self.scheme == Scheme.DATA:
            assert "," in url

        hostAndPort, url = url.split("/", 1) if "/" in url else (url, "")
        self.host, *port = hostAndPort.split(":", 1)
        if port:
            self.port = int(port[0])
        else:
            self.port = DEFAULT_PORTS.get(self.scheme, None)

        self.path = "/" + url
        # XXX: move this stuff out
        self.sockets = {}
        self.cache = {}

    def __hash__(self):
        return hash((self.scheme, self.host, self.port, self.path, self.is_viewsource))

    def __eq__(self, other):
        if not isinstance(other, URL):
            return False
        return (
            self.scheme == other.scheme
            and self.host == other.host
            and self.port == other.port
            and self.path == other.path
            and self.is_viewsource == other.is_viewsource
        )

    def num_sockets(self) -> int:
        return len(self.sockets)

    def request_response(self) -> Response:
        # XXX: some error handling
        match self.scheme:
            case Scheme.FILE:
                with open(self.path) as f:
                    response = Response(body="\n".join(f.readlines()))
            case Scheme.HTTP | Scheme.HTTPS:
                response = _handle_http(self)
            case Scheme.DATA:
                response = Response(body=self.path.split(",", 1)[1])
            case _:
                response = Response()

        return response

    def _fetch_http(self) -> IO[bytes]:
        host_port = (self.host, self.port)
        s = self.sockets.get(host_port, None)
        if s is None or s.fileno() == -1:
            s = self._init_socket(host_port)

        request = self._build_request()
        try:
            s.send(request.encode("utf8"))
        except BrokenPipeError:
            s = self._init_socket(host_port)
            s.send(request.encode("utf8"))

        raw_response = s.makefile("rb", newline="\r\n")

        return raw_response

    def _init_socket(self, host_port):
        s = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
        )
        if self.scheme == Scheme.HTTPS:
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
        s.connect(host_port)
        self.sockets[host_port] = s
        return s

    def request(self) -> str:
        response = self.request_response()
        return response.body

    def _build_request(self):
        request = f"GET {self.path} HTTP/1.1\r\n"
        request += f"Host: {self.host}\r\n"
        request += "User-Agent: Giraffe\r\n"
        request += "Accept-Encoding: gzip\r\n"
        request += "\r\n"
        return request

    def _parse_response(self, raw: IO[bytes]) -> Response:
        response = Response()
        self._parse_statusline(raw, response)
        self._parse_headers(raw, response)
        self._parse_content(raw, response)
        return response

    def _parse_statusline(self, raw: IO[bytes], response: Response):
        statusline = raw.readline().decode("utf8")
        version, status, explanation = statusline.split(" ", 2)
        response.version = version
        response.status = status
        response.explanation = explanation

    def _parse_headers(self, raw: IO[bytes], response: Response):
        response_headers = {}

        while True:
            line = raw.readline().decode("utf8")
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        if "content-encoding" in response_headers:
            assert response_headers["content-encoding"] == "gzip"

        response.headers = response_headers

    def _parse_content(self, raw: IO[bytes], response: Response):
        bbody = BytesIO()
        if self._is_chunked(response):
            while True:
                chunk_size = int(raw.readline().strip(), 16)
                if chunk_size == 0:
                    raw.readline()
                    break

                chunk = raw.read(chunk_size)
                # skip \r\n
                raw.read(2)
                bbody.write(chunk)
        else:
            content_len = int(response.headers["content-length"])
            bbody.write(raw.read(content_len))

        if self._is_gzipped(response):
            body = gzip.decompress(bbody.getvalue())
            response.body = body.decode("utf8")
        else:
            response.body = bbody.getvalue().decode("utf8")

    def _is_chunked(self, response) -> bool:
        return (
            "transfer-encoding" in response.headers
            and response.headers["transfer-encoding"] == "chunked"
        )

    def _is_gzipped(self, response) -> bool:
        return (
            "content-encoding" in response.headers
            and response.headers["content-encoding"] == "gzip"
        )

    def resolve(self, url: str) -> "URL":
        if "://" in url:
            return URL(url)
        if not url.startswith("/"):
            dir, _ = self.path.rsplit("/", 1)
            while url.startswith("../"):
                _, url = url.split("/", 1)
                if "/" in dir:
                    dir, _ = dir.rsplit("/", 1)
            url = dir + "/" + url
        if url.startswith("//"):
            return URL(self.scheme.name.lower() + ":" + url)
        else:
            return URL(
                self.scheme.name.lower()
                + "://"
                + self.host
                + ":"
                + str(self.port)
                + url
            )


# XXX Move this into browser?
def _handle_http(url: URL) -> Response:
    response = Response()
    needs_request = True
    while needs_request:
        cached = url.cache.get(url, None)
        if cached:
            max_age, response = cached
            if time.time() < max_age:
                return response

        raw = url._fetch_http()
        response = url._parse_response(raw)
        # XXX: assumes has a location header
        # TODO: handle max redirects
        if response.status == "301":
            location = response.headers["location"]
            if not location.startswith("http"):
                location = (
                    f"{url.scheme.name.lower()}://{url.host}:{url.port}{location}"
                )
            url = URL(location)
        else:
            needs_request = False

        if (
            "cache-control" in response.headers
            and "no-store" not in response.headers["cache-control"]
        ):
            ccontrol = response.headers["cache-control"]
            directives = ccontrol.split(",")
            max_age = 0
            for d in directives:
                if "max-age" in d:
                    _, max_age = d.split("=")
                    max_age = int(max_age.strip())
            if max_age:
                url.cache[url] = (time.time() + max_age, response)

    return response
