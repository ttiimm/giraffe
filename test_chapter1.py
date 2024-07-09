from chapter1 import URL

from http.server import SimpleHTTPRequestHandler
import socketserver
import threading


class TestServer(socketserver.TCPServer):
    allow_reuse_address = True

    __test__ = False # pytest should ignore this 


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


def test_request():
    httpd = TestServer(("", 8888), SimpleHTTPRequestHandler)
    httpd_thread = threading.Thread(target=httpd.serve_forever)
    httpd_thread.daemon = True
    httpd_thread.start()
    raw_url = "http://localhost:8888/data/index.html"
    url = URL(raw_url)
    
    response = url.request()
    assert response.version == "HTTP/1.0"
    assert response.status == "200"
    assert response.explanation == "OK\r\n"
    assert response.headers["content-type"] == "text/html"
    assert response.content == "<html></html>"


if __name__ == "__main__":
    test_request()