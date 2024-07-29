import math
import sys
import tkinter
import tkinter.font
from tkinter import BOTH

from giraffe.layout import VSTEP, Layout, lineheight
from giraffe.net import ABOUT_BLANK, URL
from giraffe.parser import HtmlParser, Node

"""An implementation of browser gui code for displaying web pages.

This code is based on Chapter 2 of 
[Web Browser Engineering](https://browser.engineering/graphics.html).
"""

DO_EXPAND = 1
WIDTH, HEIGHT = 800, 600
SCROLL_STEP = 100
SCROLL_MULTIPLIER = -20
SCROLLBAR_WIDTH = 12
SCROLLBAR_PAD = 4
SCROLLBAR_COLOR = "cornflower blue"


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
        self.nodes: Node = HtmlParser(ABOUT_BLANK).parse()
        self.location = ""
        self.window.bind(sequence="<Down>", func=self.scrolldown)
        self.window.bind(sequence="<Up>", func=self.scrollup)
        self.window.bind(sequence="<MouseWheel>", func=self.scrolldelta)
        self.window.bind(sequence="<Configure>", func=self.configure)

    def load(self, to_load: str):
        try:
            url = URL(to_load)
        except Exception as e:
            msg = getattr(e, "message", repr(e))
            print(f"error: {msg}", file=sys.stderr)
            url = URL("about:blank")

        body = url.request()
        self.location = url
        self.nodes = HtmlParser(body).parse(url.is_viewsource)
        # display_list is standard browser/gui (?) terminology
        self.display_list = Layout(self.nodes, self.width).display_list
        # TODO add logging
        # [print(du) for du in self.display_list]
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        self._display_text()
        self._display_scrollbar()

    def _display_text(self):
        for du in self.display_list:
            x, y, c, font = (du.cursor_x, du.cursor_y, du.word, du.font)
            if y + lineheight(font) < self.scroll:
                continue
            if y > self.scroll + self.height:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c, font=font, anchor="nw")

    def _display_scrollbar(self):
        if not self.display_list:
            return

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
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=SCROLLBAR_COLOR)

    def configure(self, e):
        self.width = e.width
        self.height = e.height
        self.display_list = Layout(
            self.nodes, self.width - SCROLLBAR_WIDTH
        ).display_list
        self.draw()

    def scrolldown(self, _e):
        self._handle_scroll(SCROLL_STEP)

    def scrollup(self, _e):
        self._handle_scroll(-SCROLL_STEP)

    def scrolldelta(self, e):
        delta = e.delta * SCROLL_MULTIPLIER
        self._handle_scroll(delta)

    def _handle_scroll(self, delta):
        lastline = self.display_list[-1]
        vstep = lineheight(lastline.font)
        maxline = lastline.cursor_y - self.height + vstep + VSTEP
        # clamp scroll such that scroll doesn't go beyond the body
        self.scroll = max(0, min(self.scroll + delta, maxline))
        self.draw()
