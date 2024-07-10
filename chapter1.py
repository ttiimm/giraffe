from typing import Mapping, IO
from dataclasses import dataclass, field
import socket
import ssl


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
        assert self.scheme in ["http", "https"]
        hostAndPort, url = url.split("/", 1) if "/" in url else (url, "")
        default_port = {"http": "80", "https": "443"}
        self.host, port = (
            hostAndPort.split(":")
            if ":" in hostAndPort
            else (hostAndPort, default_port[self.scheme])
        )
        self.port = int(port)
        self.path = "/" + url

    def request_response(self) -> Response:
        s = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
        )
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
        s.connect((self.host, self.port))

        request = self._build_request()
        s.send(request.encode("utf8"))
        raw_response = s.makefile("r", encoding="utf8", newline="\r\n")
        response = self._parse_response(raw_response)
        s.close()
        return response

    def request(self) -> str:
        response = self.request_response()
        return response.content

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


def load(url: URL):
    body = url.request()
    show(body)


def show(body: str):
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")


if __name__ == "__main__":
    import sys

    load(URL(sys.argv[1]))
