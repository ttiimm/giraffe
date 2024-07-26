import socketserver
import threading
from http.server import SimpleHTTPRequestHandler

import pytest

from giraffe.browser import Browser
from giraffe.layout import Tag
from giraffe.net import URL, Scheme

"""Test cases for the browser's net code.

These test help verify the content and exercises for Chapter 2 of
[Web Browser Engineering](https://browser.engineering/graphics.html).
"""


# TODO: record request for verification?
# XXX: avoid copy pasta
class TestServer(socketserver.TCPServer):
    allow_reuse_address = True
    __test__ = False  # pytest should ignore this


@pytest.fixture(scope="module")
def _test_server():
    httpd = TestServer(("", 8889), SimpleHTTPRequestHandler)
    httpd_thread = threading.Thread(target=httpd.serve_forever)
    httpd_thread.daemon = True
    httpd_thread.start()
    yield httpd
    httpd.shutdown()


def test_url_with_data():
    url = URL("about:blank")
    assert url.scheme == Scheme.ABOUT


def test_request_aboutblank():
    raw_url = "about:blank"
    url = URL(raw_url)

    content = url.request()
    assert content == "<html><head></head><body></body></html>"


def test_with_malformed_url():
    browser = Browser()
    browser.load("foo:bar:quux")
    assert browser.location == URL("about:blank")
    assert browser.display_list == []
    assert browser.tokens == [
        Tag("html"),
        Tag("head"),
        Tag("/head"),
        Tag("body"),
        Tag("/body"),
        Tag("/html"),
    ]
