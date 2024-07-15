import tkinter

from giraffe.net import URL

"""An implementation of browser gui code for displaying web pages.

This code is based on Chapter 2 of 
[Web Browser Engineering](https://browser.engineering/http.html).
"""


class Browser(object):
    WIDTH, HEIGHT = 800, 600

    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, width=Browser.WIDTH, height=Browser.HEIGHT
        )
        self.canvas.pack()

    def load(self, url: URL):
        body = url.request()
        self.show(body, url.is_viewsource)

    def show(self, body: str, is_viewsource=False) -> str:
        if is_viewsource:
            return body

        result = ""
        in_tag = False
        consume = 0

        for i, c in enumerate(body):
            if consume:
                consume -= 1
                continue

            if c == "<":
                in_tag = True
            elif c == ">":
                in_tag = False
            elif c == "&" and body[i : i + 4] == "&lt;":
                result += "<"
                consume += 3
            elif c == "&" and body[i : i + 4] == "&gt;":
                result += ">"
                consume += 3
            elif not in_tag:
                result += c

        return result
