from http.server import SimpleHTTPRequestHandler
import socketserver
import threading

import pytest
from giraffe.browser import WIDTH, Browser, DisplayUnit, HSTEP, VSTEP, layout, lex
from giraffe.net import URL, Scheme

"""Test cases for the browser's net code.

These test help verify the content and exercises for Chapter 2 of
[Web Browser Engineering: graphics](https://browser.engineering/graphics.html).
"""

LOREM_IPSUM = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore 
et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo 
consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. 
Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."""


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


def test_layout():
    display_list = layout("hi mom", WIDTH)
    assert [
        DisplayUnit(HSTEP * 1, VSTEP, "h"),
        DisplayUnit(HSTEP * 2, VSTEP, "i"),
        DisplayUnit(HSTEP * 3, VSTEP, " "),
        DisplayUnit(HSTEP * 4, VSTEP, "m"),
        DisplayUnit(HSTEP * 5, VSTEP, "o"),
        DisplayUnit(HSTEP * 6, VSTEP, "m"),
    ] == display_list


def test_layout_wraps():
    display_list = layout(LOREM_IPSUM, WIDTH)
    assert display_list[0] == DisplayUnit(HSTEP, VSTEP, "L")
    assert display_list[-1] == DisplayUnit(650, 216, ".")


def test_layout_newlines():
    display_list = layout("hello\nworld", WIDTH)
    assert display_list[4] == DisplayUnit(HSTEP * 5, VSTEP, "o")
    assert display_list[5] == DisplayUnit(HSTEP * 1, VSTEP * 3, "w")


# XXX: re-visit this with more examples?
def test_layout_skip_consecutive():
    display_list = layout("hello\n\nworld", WIDTH)
    assert display_list[4] == DisplayUnit(HSTEP * 5, VSTEP, "o")
    assert display_list[5] == DisplayUnit(HSTEP * 1, VSTEP * 3, "w")


def test_request_emoji(test_server):
    raw_url = "http://localhost:8888/data/emoji.html"
    url = URL(raw_url)

    content = url.request()
    # FIXME: handle emoji when encoded
    assert lex(content).strip() == "&#9924; \n&#128512; \n⛄ \n😀"


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
    assert browser.display_list == []
    assert browser.text == ""
    assert browser.location == URL("about:blank")
