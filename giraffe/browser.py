import math
import sys
import tkinter
import tkinter.font
from tkinter import BOTH
from typing import List

from giraffe.layout import (
    VSTEP,
    HSTEP,
    Command,
    DocumentLayout,
    DrawLine,
    DrawOutline,
    DrawRect,
    DrawText,
    Rect,
    get_font,
    paint_tree,
)
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
        self.window.bind(sequence="<Up>", func=self.handle_up)
        self.window.bind(sequence="<MouseWheel>", func=self.handle_wheel)
        self.window.bind(sequence="<Configure>", func=self.handle_configure)
        self.window.bind(sequence="<Button-1>", func=self.handle_click)
        self.window.bind(sequence="<Key>", func=self.handle_key)
        self.window.bind(sequence="<Return>", func=self.handle_enter)
        self.chrome = Chrome(self)

    def new_tab(self, url):
        new_tab = Tab(
            self.width,
            self.height - self.chrome.bottom,
            self.chrome.bottom,
        )
        new_tab.load(url)
        self.active_tab = new_tab
        self.tabs.append(new_tab)
        self.draw()

    def handle_down(self, _e):
        self.active_tab.scrolldown()
        self.draw()

    def handle_up(self, _e):
        self.active_tab.scrollup()
        self.draw()

    def handle_wheel(self, e):
        self.active_tab.scrolldelta(e)
        self.draw()

    def handle_click(self, e):
        if e.y < self.chrome.bottom:
            self.chrome.click(e.x, e.y)
        else:
            self.active_tab.click(e.x, e.y)
        self.draw()

    def handle_configure(self, e):
        self.width = e.width
        self.height = e.height
        self.active_tab.configure(self.width, self.height + self.chrome.bottom)
        self.draw()
    
    def handle_key(self, e):
        if len(e.char) == 0: 
            return
        if not (0x20 <= ord(e.char) < 0x7f):
            return
        self.chrome.keypress(e.char)
        self.draw()
    
    def handle_enter(self, e):
        self.chrome.enter()
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        self.active_tab.draw(self.canvas)
        for cmd in self.chrome.paint(self.width):
            cmd.execute(0, self.canvas)


class Chrome:
    def __init__(self, browser):
        self.browser = browser
        self.font = get_font("Iosevka", 20, False, False)
        self.font_height = self.font.metrics("linespace")
        self.padding = 5
        self.tabbar_top = 0
        self.tabbar_bottom = self.font_height + 2 * self.padding

        plus_width = self.font.measure("+") + 2 * self.padding
        self.newtab_rect = Rect(
            self.padding,
            self.padding,
            self.padding + plus_width,
            self.padding + self.font_height,
        )
        self.urlbar_top = self.tabbar_bottom
        self.urlbar_bottom = self.urlbar_top + self.font_height + 2 * self.padding
        self.bottom = self.urlbar_bottom
        back_width = self.font.measure("<") + 2 * self.padding
        self.back_rect = Rect(
            self.padding,
            self.urlbar_top + self.padding,
            self.padding + back_width,
            self.urlbar_bottom - self.padding,
        )
        self.address_rect = Rect(
            self.back_rect.top + self.padding,
            self.urlbar_top + self.padding,
            WIDTH - self.padding,
            self.urlbar_bottom - self.padding,
        )
        self.focus = None
        self.address_bar = ""

    def tab_rect(self, i):
        tabs_start = self.newtab_rect.right + self.padding
        tabs_width = self.font.measure("Tab X") + 2 * self.padding
        return Rect(
            tabs_start + tabs_width * i,
            self.tabbar_top,
            tabs_start + tabs_width * (i + 1),
            self.tabbar_bottom,
        )

    def paint(self, width: int):
        cmds = []
        cmds.append(
            DrawRect(left=0, top=0, right=width, bottom=self.bottom, color="white")
        )
        cmds.append(DrawLine(0, self.bottom, width, self.bottom, "black", 1))
        cmds.append(DrawOutline(self.newtab_rect, "black", 1))
        cmds.append(
            DrawText(
                text="+",
                font=self.font,
                color="black",
                left=self.newtab_rect.left + self.padding,
                top=self.newtab_rect.top,
            )
        )

        for i, tab in enumerate(self.browser.tabs):
            bounds = self.tab_rect(i)
            cmds.append(
                DrawLine(bounds.left, 0, bounds.left, bounds.bottom, "black", 1)
            )
            cmds.append(
                DrawLine(bounds.right, 0, bounds.right, bounds.bottom, "black", 1)
            )
            cmds.append(
                DrawText(
                    text=f"Tab {i}",
                    font=self.font,
                    color="black",
                    left=bounds.left + self.padding,
                    top=bounds.top + self.padding,
                )
            )

            if tab == self.browser.active_tab:
                cmds.append(
                    DrawLine(0, bounds.bottom, bounds.left, bounds.bottom, "black", 1)
                )
                cmds.append(
                    DrawLine(
                        bounds.right, bounds.bottom, WIDTH, bounds.bottom, "black", 1
                    )
                )

        cmds.append(DrawOutline(self.back_rect, "black", 1))
        cmds.append(
            DrawText(
                text="<",
                font=self.font,
                color="black",
                left=self.back_rect.left + self.padding,
                top=self.back_rect.top,
            )
        )
        cmds.append(DrawOutline(self.address_rect, "black", 1))
        if self.focus == "address bar":
            url = self.address_bar
            w = self.font.measure(self.address_bar)
            cmds.append(
                DrawLine(
                    self.address_rect.left + self.padding + w,
                    self.address_rect.top,
                    self.address_rect.left + self.padding + w,
                    self.address_rect.bottom,
                    "red",
                    1,
                )
            )
        else:
            url = str(self.browser.active_tab.location)
        cmds.append(
            DrawText(
                text=url,
                font=self.font,
                color="black",
                left=self.address_rect.left + self.padding,
                top=self.back_rect.top,
            )
        )

        return cmds

    def click(self, x, y):
        self.focus = None
        if self.newtab_rect.contains_point(x, y):
            self.browser.new_tab(URL("https://browser.engineering/"))
        elif self.back_rect.contains_point(x, y):
            self.browser.active_tab.go_back()
        elif self.address_rect.contains_point(x, y):
            self.focus = "address bar"
            self.address_bar = ""
        else:
            for i, tab in enumerate(self.browser.tabs):
                if self.tab_rect(i).contains_point(x, y):
                    self.browser.active_tab = tab
                    break
    
    def keypress(self, char):
        if self.focus == "address bar":
            self.address_bar += char
    
    def enter(self):
        if self.focus == "address bar":
            self.browser.active_tab.load(self.address_bar)
            self.focus = None


class Tab:
    def __init__(self, width: int, height: int, tab_height: int):
        self.width = width
        self.height = height
        self.tab_height = tab_height
        # XXX: this is a hack to get the tab to display correctly on load...
        self.scroll = -tab_height
        self.display_list: List[Command] = []
        self.nodes: Node = HtmlParser(ABOUT_BLANK).parse()
        self.location = URL("about:blank")
        self.rules = DEFAULT_STYLE_SHEET.copy()
        self.history: List[URL] = []

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

        self.history.append(url)
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
        self.document = DocumentLayout(
            self.nodes, self.width - SCROLLBAR_WIDTH - 2 * SCROLLBAR_PAD
        )
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

        first_y = self.document.y
        last_y = self.document.height
        if first_y < self.scroll or last_y > self.scroll + self.height:
            total_screens = math.ceil(last_y / self.height)
            scrollbar_len = self.height / total_screens
            scroll_perc = self.scroll / last_y
            x1 = self.width - SCROLLBAR_WIDTH - SCROLLBAR_PAD
            y1 = scroll_perc * self.height + self.tab_height + 2 * SCROLLBAR_PAD
            x2 = self.width - SCROLLBAR_PAD
            y2 = (
                scroll_perc * self.height
                + self.tab_height
                + scrollbar_len
                - 2 * SCROLLBAR_PAD
            )
            canvas.create_rectangle(x1, y1, x2, y2, fill=SCROLLBAR_COLOR)

    def configure(self, width, height):
        self.width = width
        self.height = height
        self._build_display_list()

    def scrolldown(self):
        self._handle_scroll(SCROLL_STEP)

    def scrollup(self):
        self._handle_scroll(-SCROLL_STEP)

    def scrolldelta(self, e):
        delta = e.delta * SCROLL_MULTIPLIER
        self._handle_scroll(delta)

    def _handle_scroll(self, delta):
        # clamp scroll such that scroll doesn't go beyond the body
        max_y = max(self.document.height + 2 * VSTEP - self.height, 0)
        min_y = min(self.scroll + delta, max_y)
        self.scroll = max(-self.tab_height, min_y)

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

    def go_back(self):
        if len(self.history) > 1:
            self.history.pop()
            back = self.history.pop()
            self.load(back)


def tree_to_list(tree, list: List):
    list.append(tree)
    for child in tree.children:
        tree_to_list(child, list)
    return list
