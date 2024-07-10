from typing import Mapping, IO
from dataclasses import dataclass, field
import os
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
        assert self.scheme in ["http", "https", "file"]
        hostAndPort, url = url.split("/", 1) if "/" in url else (url, "")
        default_port = {"http": "80", "https": "443", "file": ""}
        self.host, port = (
            hostAndPort.split(":")
            if ":" in hostAndPort
            else (hostAndPort, default_port[self.scheme])
        )
        if port:
            self.port = int(port)
        else:
            # XXX: is this right?
            self.port = ""
        self.path = "/" + url

    def request_response(self) -> Response:
        # XXX: some error handling
        response = Response()
        match self.scheme:
            case "file":
                with open(self.path) as f:
                    response = Response(content="\n".join(f.readlines()))
            case "http":
                raw_response = self.fetch_http()
                response = self._parse_response(raw_response)
            case "https":
                raw_response = self.fetch_http()
                response = self._parse_response(raw_response)

        return response

    def fetch_http(self):
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
        s.close()
        return raw_response

    def request(self) -> str:
        response = self.request_response()
        return response.content

    def _build_request(self):
        request = f"GET {self.path} HTTP/1.0\r\n"
        request += f"Host: {self.host}\r\n"
        request += "Connection: close\r\n"
        request += "User-Agent: Giraffe\r\n"
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

    if len(sys.argv) >= 2:
        url = sys.argv[1]
    else:
        # XXX: changeme to better default
        url = f"file://{os.getcwd()}/data/index.html"
    load(URL(url))
