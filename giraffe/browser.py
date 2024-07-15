from dataclasses import dataclass
import tkinter
from typing import List

from giraffe.net import URL

"""An implementation of browser gui code for displaying web pages.

This code is based on Chapter 2 of 
[Web Browser Engineering](https://browser.engineering/http.html).
"""

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100


@dataclass
class DisplayUnit:
    cursor_x: int
    cursor_y: int
    c: str


class Browser(object):
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()
        self.scroll = 0
        self.display_list = []
        self.window.bind(sequence="<Down>", func=self.scrolldown)
        self.window.bind(sequence="<Up>", func=self.scrollup)

    def load(self, url: URL):
        body = url.request()
        text = lex(body, url.is_viewsource)
        # display_list is standard browser/gui (?) terminology
        self.display_list = layout(text)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for du in self.display_list:
            x, y, c = (du.cursor_x, du.cursor_y, du.c)
            if y + VSTEP < self.scroll:
                continue
            if y > self.scroll + HEIGHT:
                continue

            self.canvas.create_text(x, y - self.scroll, text=c)

    def scrolldown(self, _e):
        self.scroll += SCROLL_STEP
        self.draw()

    def scrollup(self, _e):
        self.scroll -= SCROLL_STEP
        self.draw()


def lex(body: str, is_viewsource=False) -> str:
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


def layout(text) -> List[DisplayUnit]:
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        display_list.append(DisplayUnit(cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if cursor_x >= WIDTH - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP
    return display_list
