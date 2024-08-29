import math
import sys
import tkinter
import tkinter.font
from tkinter import BOTH
from typing import List

from giraffe.layout import VSTEP, Command, DocumentLayout, paint_tree
from giraffe.net import ABOUT_BLANK, URL
from giraffe.parser import Element, HtmlParser, Node, Text
from giraffe.styling import DEFAULT_STYLE_SHEET, CSSParser, style

"""An implementation of browser gui code for displaying web pages.

This code is based on Chapter 2 and Chapter 7 of 
[Web Browser Engineering - Graphics](https://browser.engineering/graphics.html)
[Web Browser Engineering - Chrome](https://browser.engineering/chrome.html).
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


class Browser:
    def __init__(self):
        self.tabs: List["Tab"] = []
        self.active_tab: "Tab | None" = None
        self.width = WIDTH
        self.height = HEIGHT
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, width=self.width, height=self.height, bg="white"
        )
        self.canvas.pack(fill=BOTH, expand=DO_EXPAND)
        self.window.bind(sequence="<Down>", func=self.handle_down)
        # self.window.bind(sequence="<Up>", func=self.scrollup)
        # self.window.bind(sequence="<MouseWheel>", func=self.scrolldelta)
        # self.window.bind(sequence="<Configure>", func=self.configure)
        self.window.bind(sequence="<Button-1>", func=self.handle_click)

    def new_tab(self, url):
        new_tab = Tab(self.width, self.height)
        new_tab.load(url)
        self.active_tab = new_tab
        self.tabs.append(new_tab)
        self.draw()

    def handle_down(self, _e):
        self.active_tab.scrolldown()
        self.draw()
    
    def handle_click(self, e):
        self.active_tab.click(e.x, e.y)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        self.active_tab.draw(self.canvas)



class Tab(object):
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.scroll = 0
        self.display_list: List[Command] = []
        self.nodes: Node = HtmlParser(ABOUT_BLANK).parse()
        self.location = URL("about:blank")
        self.rules = DEFAULT_STYLE_SHEET.copy()

    def load(self, to_load: str | URL):
        if isinstance(to_load, str):
            try:
                url = URL(to_load)
            except Exception as e:
                msg = getattr(e, "message", repr(e))
                print(f"error: {msg}", file=sys.stderr)
                url = URL("about:blank")
        else:
            url = to_load

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

    def _build_display_list(self):
        style(self.nodes, self.rules)
        self.document = DocumentLayout(self.nodes, self.width)
        self.document.layout()
        # display_list is standard browser/gui (?) terminology
        self.display_list = []
        paint_tree(self.document, self.display_list)

    def draw(self, canvas):
        self._display_text(canvas)
        self._display_scrollbar(canvas)

    def _display_text(self, canvas):
        for cmd in self.display_list:
            if cmd.top > self.scroll + self.height:
                continue
            if cmd.bottom < self.scroll:
                continue

            cmd.execute(self.scroll, canvas)

    def _display_scrollbar(self, canvas):
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
            canvas.create_rectangle(x1, y1, x2, y2, fill=SCROLLBAR_COLOR)


    def configure(self, e):
        self.width = e.width
        self.height = e.height
        self._build_display_list()

    def scrolldown(self):
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

    def click(self, x: int, y: int):
        y += self.scroll
        objs = [
            obj
            for obj in tree_to_list(self.document, [])
            if obj.x <= x < obj.x + obj.width and obj.y <= y < obj.y + obj.height
        ]
        if not objs:
            return
        element = objs[-1].node
        while element:
            if isinstance(element, Text):
                pass
            elif element.tag == "a" and "href" in element.attributes:
                url = self.location.resolve(element.attributes["href"])
                return self.load(url)
            element = element.parent


def tree_to_list(tree, list: List):
    list.append(tree)
    for child in tree.children:
        tree_to_list(child, list)
    return list
