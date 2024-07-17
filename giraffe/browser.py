from dataclasses import dataclass
import math
import tkinter
from tkinter import BOTH
from typing import List

from giraffe.net import URL

"""An implementation of browser gui code for displaying web pages.

This code is based on Chapter 2 of 
[Web Browser Engineering](https://browser.engineering/http.html).
"""

DO_EXPAND = 1
WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
SCROLL_MULTIPLIER = -20
SCROLLBAR_WIDTH = 12
SCROLLBAR_PAD = 4
SCROLLBAR_COLOR = "cornflower blue"


@dataclass
class DisplayUnit:
    cursor_x: int
    cursor_y: int
    c: str


class FakeEvent:
    delta: int


class Browser(object):
    def __init__(self):
        self.window = tkinter.Tk()
        self.width = WIDTH
        self.height = HEIGHT
        self.canvas = tkinter.Canvas(self.window, width=self.width, height=self.height)
        self.canvas.pack(fill=BOTH, expand=DO_EXPAND)
        self.scroll = 0
        self.display_list = []
        self.text = ""
        self.window.bind(sequence="<Down>", func=self.scrolldown)
        self.window.bind(sequence="<Up>", func=self.scrollup)
        self.window.bind(sequence="<MouseWheel>", func=self.scrolldelta)
        self.window.bind(sequence="<Configure>", func=self.configure)

    def load(self, url: URL):
        body = url.request()
        self.text = lex(body, url.is_viewsource)
        # display_list is standard browser/gui (?) terminology
        self.display_list = layout(self.text, self.width)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        self._display_text()
        self._display_scrollbar()

    def _display_text(self):
        for du in self.display_list:
            x, y, c = (du.cursor_x, du.cursor_y, du.c)
            if y + VSTEP < self.scroll:
                continue
            if y > self.scroll + self.height:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def _display_scrollbar(self):
        first_y = self.display_list[0].cursor_y
        last_y = self.display_list[-1].cursor_y
        if first_y < self.scroll or last_y > self.scroll + self.height:
            total_screens = math.ceil(last_y / self.height)
            scrollbar_len = self.height / total_screens
            scroll_perc = self.scroll / last_y
            x1 = self.width - SCROLLBAR_WIDTH
            y1 = scroll_perc * self.height + SCROLLBAR_PAD
            x2 = self.width - SCROLLBAR_PAD
            y2 = scroll_perc * self.height + scrollbar_len - SCROLLBAR_PAD
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=SCROLLBAR_COLOR, stipple='gray25')

    def configure(self, e):
        needs_draw = False
        if self.width != e.width:
            self.width = e.width
            self.display_list = layout(self.text, self.width - SCROLLBAR_WIDTH)
            needs_draw = True
        if self.height != e.height:
            self.height = e.height

        if needs_draw:
            self.draw()

    def scrolldown(self, _e):
        self._handle_scroll(SCROLL_STEP)

    def scrollup(self, _e):
        self._handle_scroll(-SCROLL_STEP)

    def scrolldelta(self, e):
        delta = e.delta * SCROLL_MULTIPLIER
        self._handle_scroll(delta)

    def _handle_scroll(self, delta):
        maxline = self.display_list[-1].cursor_y - self.height
        # clamp scroll such that scroll doesn't go beyond the body
        self.scroll = max(0, min(self.scroll + delta, maxline))
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


def layout(text, width) -> List[DisplayUnit]:
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    prev_c = ""
    for c in text:
        if c == "\n":
            # XXX: skip over repeating new lines characters
            if prev_c == "\n":
                continue
            cursor_y += VSTEP * 2
            cursor_x = HSTEP
        else:
            display_list.append(DisplayUnit(cursor_x, cursor_y, c))
            cursor_x += HSTEP
            if cursor_x >= width - HSTEP:
                cursor_y += VSTEP
                cursor_x = HSTEP

        prev_c = c
    return display_list
