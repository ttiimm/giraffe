import socketserver
import threading
from http.server import SimpleHTTPRequestHandler

import pytest

from giraffe.browser import Browser
from giraffe.net import URL

"""Test cases for the browser's net code.

These test help verify the content and exercises for Chapter 2 of
[Web Browser Engineering](https://browser.engineering/graphics.html).
"""

# TODO: work on more tests for CH2
# TODO: snapshot tests?


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


def test_with_malformed_url():
    browser = Browser()
    browser.new_tab("foo:bar:quux")
    assert browser.active_tab
    assert browser.active_tab.location == URL("about:blank")
    assert browser.active_tab.display_list == []
    assert str(browser.active_tab.nodes) == "<html><head></head><body></body></html>"


def test_load(_test_server):
    browser = Browser()
    browser.new_tab("http://0.0.0.0:8889/data/index.html")
    assert browser.active_tab
    assert browser.active_tab.location == URL("http://0.0.0.0:8889/data/index.html")
    assert browser.active_tab.display_list
    assert str(browser.active_tab.nodes) == "<html><body>hi</body></html>"
