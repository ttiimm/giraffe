import socket

class URL:
    
    def __init__(self, url):
        self.scheme, url = url.split("://", 1)
        assert self.scheme == "http"
        self.host, url = url.split("/", 1)
        self.path = "/" + url

    def request(self):
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP
        )
        s.connect((self.host, 80))
        
        request = self._build_request()
        s.send(request.encode("utf8"))
        response = s.makefile("r", encoding="utf8", newline="\r\n")
        version, status, explanation = self._parse_response(response)

    def _build_request(self):
        request = f"GET {self.path} HTTP/1.0\r\n"
        request += f"Host: {self.host}\r\n"
        request += "\r\n"
        return request
    
    def _parse_response(self, response):
        version, status, explanation = self._parse_statusline(response)
        headers = self._parse_headers(response)

        return version, status, explanation
        
    def _parse_statusline(self, response):
        statusline = response.readline()
        return statusline.split(" ", 2)
    
    def _parse_headers(self, response):
        response_headers = {}

        while True:
            line = response.readline()
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers
        return response_headers

