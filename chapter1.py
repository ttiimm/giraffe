from typing import Mapping, IO
from dataclasses import dataclass, field
import socket


@dataclass
class Response:
    version: str = ""
    status: str = ""
    explanation: str = ""
    # XXX: can this be a [str, List[str]]
    headers: Mapping[str, str] = field(default_factory=dict)
    content: str = ""


class URL:
    def __init__(self, url: str):
        self.scheme, url = url.split("://", 1)
        assert self.scheme == "http"
        hostAndPort, url = url.split("/", 1) if "/" in url else (url, "")
        self.host, port = hostAndPort.split(":") if ":" in hostAndPort else (hostAndPort, "80")
        self.port = int(port)
        self.path = "/" + url

    def request(self):
        s = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
        )
        s.connect((self.host, self.port))

        request = self._build_request()
        s.send(request.encode("utf8"))
        raw_response = s.makefile("r", encoding="utf8", newline="\r\n")
        return self._parse_response(raw_response)

    def _build_request(self):
        request = f"GET {self.path} HTTP/1.0\r\n"
        request += f"Host: {self.host}\r\n"
        request += "\r\n"
        return request

    def _parse_response(self, raw: IO[str]) -> Response:
        response = Response()
        self._parse_statusline(raw, response)
        self._parse_headers(raw, response)
        self._parse_content(raw, response)
        return response

    def _parse_statusline(self, raw: IO[str], response: Response):
        statusline = raw.readline()
        version, status, explanation = statusline.split(" ", 2)
        response.version = version
        response.status = status
        response.explanation = explanation
        return response

    def _parse_headers(self, raw: IO[str], response: Response):
        response_headers = {}

        while True:
            line = raw.readline()
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers
        response.headers = response_headers

    def _parse_content(self, raw: IO[str], response: Response):
        response.content = raw.read()
