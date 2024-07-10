from chapter1 import URL

from http.server import SimpleHTTPRequestHandler
import pytest
import socketserver
import threading


class TestServer(socketserver.TCPServer):
    allow_reuse_address = True

    __test__ = False  # pytest should ignore this


@pytest.fixture(scope="module")
def test_server():
    httpd = TestServer(("", 8888), SimpleHTTPRequestHandler)
    httpd_thread = threading.Thread(target=httpd.serve_forever)
    httpd_thread.daemon = True
    httpd_thread.start()
    yield httpd
    httpd.shutdown()


def test_url_of_exampleorg():
    url = URL("http://example.org/")
    assert url.host == "example.org"
    assert url.port == 80


def test_url_with_host_port():
    url = URL("http://127.0.0.1:1234/")
    assert url.host == "127.0.0.1"
    assert url.port == 1234


def test_url_of_exampleorg_no_slash():
    url = URL("http://example.org")
    assert url.host == "example.org"


def test_url_with_path():
    url = URL("http://example.org/my/path")
    assert url.host == "example.org"
    assert url.port == 80
    assert url.path == "/my/path"


def test_url_with_https():
    url = URL("https://example.org")
    assert url.scheme == "https"
    assert url.port == 443


def test_request(test_server):
    raw_url = "http://localhost:8888/data/index.html"
    url = URL(raw_url)

    response = url.request_response()
    assert response.version == "HTTP/1.0"
    assert response.status == "200"
    assert response.explanation == "OK\r\n"
    assert response.headers["content-type"] == "text/html"
    assert response.content == "<html></html>"


def test_request_content():
    raw_url = "http://localhost:8888/data/index.html"
    url = URL(raw_url)

    content = url.request()
    assert content == "<html></html>"
