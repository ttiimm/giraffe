from chapter1 import URL
from io import StringIO

YIKES = """HTTP/1.0 200 OK
Accept-Ranges: bytes
Age: 422085
Cache-Control: max-age=604800
Content-Type: text/html; charset=UTF-8
Date: Tue, 09 Jul 2024 15:38:33 GMT
Etag: "3147526947+gzip"
Expires: Tue, 16 Jul 2024 15:38:33 GMT
Last-Modified: Thu, 17 Oct 2019 07:18:26 GMT
Server: ECAcc (nyd/D169)
Vary: Accept-Encoding
X-Cache: HIT
Content-Length: 1256
Connection: close

<!doctype html>
<html>
</html>
"""


def test_url_of_exampleorg():
    url = URL("http://example.org/")
    assert url.host == "example.org"

# def test_url_of_exampleorg_no_slash():
#     url = URL("http://example.org")
#     assert url.host == "example.org"
    
def test_url_with_path():
    url = URL("http://example.org/my/path")
    assert url.path == "/my/path"
    
def test_build_request():
    url = URL("http://example.org/index.html/")
    assert url._build_request() == "GET /index.html/ HTTP/1.0\r\nHost: example.org\r\n\r\n"
    
def test_parse_statusline():
    url = URL("http://example.org/index.html/")
    test_response = StringIO(YIKES, newline="\r\n")
    version, status, explanation = url._parse_statusline(test_response)
    assert version == "HTTP/1.0"
    assert status == "200"
    assert explanation == "OK\r\n"

def test_parse_headers():
    url = URL("http://example.org/index.html/")
    test_response = StringIO(YIKES, newline="\r\n")
    test_response.readline()
    headers = url._parse_headers(test_response)
    
    assert headers["content-type"] == "text/html; charset=UTF-8"

