import math
import sys
import tkinter
import tkinter.font
from tkinter import BOTH
from typing import List

from giraffe.layout import VSTEP, Command, DocumentLayout, paint_tree
from giraffe.net import ABOUT_BLANK, URL
from giraffe.parser import Element, HtmlParser, Node
from giraffe.styling import DEFAULT_STYLE_SHEET, CSSParser, style

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
        self.canvas = tkinter.Canvas(
            self.window, width=self.width, height=self.height, bg="white"
        )
        self.canvas.pack(fill=BOTH, expand=DO_EXPAND)
        self.scroll = 0
        self.display_list: List[Command] = []
        self.nodes: Node = HtmlParser(ABOUT_BLANK).parse()
        self.location = ""
        self.rules = DEFAULT_STYLE_SHEET.copy()
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
        links = [
            node.attributes["href"]
            for node in tree_to_list(self.nodes, [])
            if isinstance(node, Element)
            and node.tag == "link"
            and node.attributes.get("rel") == "stylesheet"
            and "href" in node.attributes
        ]
        self.rules = DEFAULT_STYLE_SHEET.copy()
        for link in links:
            style_url = url.resolve(link)
            try:
                body = style_url.request()
            except:
                continue
            self.rules.extend(CSSParser(body).parse())
        self.rules = sorted(self.rules, key=lambda r: r.cascade_priority())
        self._build_display_list()
        # TODO add logging
        # [print(du) for du in self.display_list]
        self.draw()

    def _build_display_list(self):
        style(self.nodes, self.rules)
        self.document = DocumentLayout(self.nodes, self.width)
        self.document.layout()
        # display_list is standard browser/gui (?) terminology
        self.display_list = []
        paint_tree(self.document, self.display_list)

    def draw(self):
        self.canvas.delete("all")
        self._display_text()
        self._display_scrollbar()

    def _display_text(self):
        for cmd in self.display_list:
            if cmd.top > self.scroll + self.height:
                continue
            if cmd.bottom < self.scroll:
                continue

            cmd.execute(self.scroll, self.canvas)

    def _display_scrollbar(self):
        if not self.display_list:
            return

        first_y = self.display_list[0].top
        last_y = self.display_list[-1].bottom
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
        self._build_display_list()
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
        maxline = lastline.bottom - self.height - VSTEP
        # clamp scroll such that scroll doesn't go beyond the body
        self.scroll = max(0, min(self.scroll + delta, maxline))
        self.draw()


def tree_to_list(tree, list: List):
    list.append(tree)
    for child in tree.children:
        tree_to_list(child, list)
    return list
