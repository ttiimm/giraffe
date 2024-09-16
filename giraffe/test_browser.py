import socketserver
import threading
import tkinter
from http.server import SimpleHTTPRequestHandler

import pytest

from giraffe.browser import TAG_SCROLLBAR, Browser, Tab
from giraffe.layout import TAG_TEXT
from giraffe.net import URL

"""Test cases for the browser's net code.

These test help verify the content and exercises for Chapter 2 of
[Web Browser Engineering](https://browser.engineering/graphics.html).
"""

TEST_WIDTH = 50
TEST_HEIGHT = 50
TEST_CHROME_HEIGHT = 2
TK_TEXT = "text"

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


@pytest.fixture(scope="session")
def tk_window():
    window = tkinter.Tk()
    yield window
    pass


def test_with_malformed_url():
    browser = Browser()
    browser.new_tab("foo:bar:quux")
    assert browser.active_tab.location == URL("about:blank")
    assert browser.active_tab.display_list == []
    assert str(browser.active_tab.nodes) == "<html><head></head><body></body></html>"


def test_new_tab(_test_server):
    browser = Browser()
    browser.new_tab("http://0.0.0.0:8889/data/index.html")
    assert browser.active_tab.location == URL("http://0.0.0.0:8889/data/index.html")
    assert browser.active_tab.display_list
    assert str(browser.active_tab.nodes) == "<html><body>hi</body></html>"
    assert browser.height > browser.active_tab.height


def test_multi_tabs():
    browser = Browser()
    browser.new_tab("data:text/html,Hello tab 1")
    browser.new_tab("data:text/html,Hello tab 2")
    assert str(browser.active_tab.location) == "data:text/html,Hello tab 2"
    assert len(browser.tabs) == 2


def test_tab_draw_no_scroll(tk_window):
    canvas = tkinter.Canvas(tk_window, width=TEST_WIDTH, height=TEST_HEIGHT)
    tab = Tab(TEST_WIDTH, TEST_HEIGHT, TEST_CHROME_HEIGHT)
    tab.load("data:text/html,<p>hi</p>")
    tab.draw(canvas)
    text_objs = canvas.find_withtag(TAG_TEXT)
    assert len(text_objs) == 1
    text_id = text_objs[0]
    content = canvas.itemcget(text_id, TK_TEXT)
    assert content == "hi"
    scroll_bar_objs = canvas.find_withtag(TAG_SCROLLBAR)
    assert len(scroll_bar_objs) == 0


def test_tab_draw_scrollbar(tk_window):
    canvas = tkinter.Canvas(tk_window, width=TEST_WIDTH, height=TEST_HEIGHT)
    tab = Tab(TEST_WIDTH, TEST_HEIGHT, TEST_CHROME_HEIGHT)
    tab.load("data:text/html,<p>hi</p><p>hi</p>")
    tab.draw(canvas)
    text_objs = canvas.find_withtag(TAG_TEXT)
    assert len(text_objs) == 1
    text_id = text_objs[0]
    content = canvas.itemcget(text_id, TK_TEXT)
    assert content == "hi"
    scroll_bar_objs = canvas.find_withtag(TAG_SCROLLBAR)
    assert len(scroll_bar_objs) == 1
