import os
import socketserver
import threading
import time
from http.server import SimpleHTTPRequestHandler

import pytest

from giraffe.net import URL, Scheme

"""Test cases for the browser's net code.

These test help verify the content and exercises for Chapter 1 of
[Web Browser Engineering](https://browser.engineering/http.html).
"""


# TODO: record request for verification?
# XXX: avoid copy pasta
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


def test_nonexistent_scheme():
    with pytest.raises(KeyError):
        URL("foo://bar/quux")


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
    assert url.scheme == Scheme.HTTPS
    assert url.port == 443


def test_url_with_file():
    url = URL(f"file://{os.getcwd()}/data/index.html")
    assert url.scheme == Scheme.FILE
    assert url.path == f"{os.getcwd()}/data/index.html"


def test_url_with_data():
    url = URL("data:text/html,Hello world!")
    assert url.scheme == Scheme.DATA


def test_url_with_data_nocomma():
    with pytest.raises(AssertionError):
        URL("data:text/htmlHello world!")


def test_request_response(test_server):
    raw_url = "http://localhost:8888/data/index.html"
    url = URL(raw_url)

    response = url.request_response()
    assert response.version == "HTTP/1.0"
    assert response.status == "200"
    assert response.explanation == "OK\r\n"
    assert response.headers["content-type"] == "text/html"
    assert response.body == "<html>hi</html>"
    assert url.num_sockets() == 1


def test_request(test_server):
    raw_url = "http://localhost:8888/data/index.html"
    url = URL(raw_url)

    content = url.request()
    assert content == "<html>hi</html>"


@pytest.mark.slow
def test_request_headers():
    raw_url = "https://httpbin.org/headers"
    url = URL(raw_url)
    response = url.request()
    assert '"Host": "httpbin.org' in response
    assert '"User-Agent": "Giraffe"' in response


@pytest.mark.slow
def test_request_browserengineering():
    raw_url = "http://browser.engineering/http.html"
    url = URL(raw_url)
    response = url.request_response()
    assert "200" == response.status
    assert "</html>" in response.body


@pytest.mark.slow
def test_request_redirect():
    raw_url = "http://browser.engineering/redirect"
    url = URL(raw_url)
    response = url.request_response()
    assert "200" == response.status


@pytest.mark.slow
def test_request_redirect2():
    raw_url = "http://browser.engineering/redirect2"
    url = URL(raw_url)
    response = url.request_response()
    assert "200" == response.status


@pytest.mark.slow
def test_request_redirect3():
    raw_url = "http://browser.engineering/redirect3"
    url = URL(raw_url)
    response = url.request_response()
    assert "200" == response.status


def test_file_scheme():
    raw_url = f"file:///{os.getcwd()}/data/index.html"
    url = URL(raw_url)
    content = url.request()
    assert content == "<html>hi</html>"


def test_data_scheme():
    raw_url = "data:text/html,Hello world!"
    url = URL(raw_url)
    content = url.request()
    assert content == "Hello world!"


def test_data_entities():
    raw_url = "data:text/html,&lt;div&gt;"
    url = URL(raw_url)
    content = url.request()
    assert content == "&lt;div&gt;"


def test_view_source_scheme(test_server):
    raw_url = "view-source:http://localhost:8888/data/index.html"
    url = URL(raw_url)

    content = url.request()
    assert content == "<html>hi</html>"
    assert url.is_viewsource


@pytest.mark.slow
def test_caching():
    url = URL("http://example.org/index.html")
    first = url.request_response()
    second = url.request_response()
    assert first is second


@pytest.mark.slow
def test_caching_expires():
    url = URL("https://httpbin.org/cache/1")
    first = url.request_response()
    time.sleep(1)
    second = url.request_response()
    assert first is not second


def test_request_aboutblank():
    raw_url = "about:blank"
    url = URL(raw_url)

    content = url.request()
    assert content == "<html><head></head><body></body></html>"


def test_url_with_aboutblank():
    url = URL("about:blank")
    assert url.scheme == Scheme.ABOUT


def test_url_resolve_with_all_parts():
    url = URL("http://browser.engineering/http.html")
    css_url = url.resolve("http://browser.engineering/book.css")
    assert css_url.scheme == Scheme.HTTP
    assert css_url.host == "browser.engineering"
    assert css_url.port == 80
    assert css_url.path == "/book.css"


def test_url_resolve_with_host_relative():
    url = URL("http://browser.engineering/http.html")
    css_url = url.resolve("/book.css")
    assert css_url.scheme == Scheme.HTTP
    assert css_url.host == "browser.engineering"
    assert css_url.port == 80
    assert css_url.path == "/book.css"


def test_url_resolve_with_path_relative():
    url = URL("http://browser.engineering/http.html")
    css_url = url.resolve("book.css")
    assert css_url.scheme == Scheme.HTTP
    assert css_url.host == "browser.engineering"
    assert css_url.port == 80
    assert css_url.path == "/book.css"


def test_url_resolve_with_scheme_relative():
    url = URL("http://browser.engineering/http.html")
    css_url = url.resolve("//browser.engineering/book.css")
    assert css_url.scheme == Scheme.HTTP
    assert css_url.host == "browser.engineering"
    assert css_url.port == 80
    assert css_url.path == "/book.css"


def test_url_resolve_with_relative():
    url = URL("http://browser.engineering/foo/http.html")
    css_url = url.resolve("../book.css")
    assert css_url.scheme == Scheme.HTTP
    assert css_url.host == "browser.engineering"
    assert css_url.port == 80
    assert css_url.path == "/book.css"


def test_url_str_http():
    url = URL("http://browser.engineering/foo/http.html")
    assert str(url) == "http://browser.engineering/foo/http.html"


def test_url_str_https():
    url = URL("https://browser.engineering/foo/http.html")
    assert str(url) == "https://browser.engineering/foo/http.html"


def test_url_str_http_default_port():
    url = URL("http://browser.engineering:80/foo/http.html")
    assert str(url) == "http://browser.engineering/foo/http.html"


def test_url_str_https_default_port():
    url = URL("https://browser.engineering:443/foo/http.html")
    assert str(url) == "https://browser.engineering/foo/http.html"


def test_url_str_data():
    url = URL("data:text/html,Hello world!")
    assert str(url) == "data:text/html,Hello world!"
