from enum import Enum
import math
import tkinter.font
from dataclasses import dataclass
from typing import List, Literal

from giraffe.parser import SOFT_HYPHEN, Element, Node, Text

"""The layout code used by the browser.

This code is based on Chapter 3/5 of 
[Web Browser Engineering](https://browser.engineering/).
"""


HSTEP, VSTEP = 13, 18

WEIGHT_NORMAL = "normal"
WEIGHT_BOLD = "bold"
SLANT_ROMAN = "roman"
SLANT_ITALIC = "italic"


@dataclass
class Styling:
    font: tkinter.font.Font
    color: str = "black"
    valignment: Literal["None", "Top"] = "None"


@dataclass
class LineUnit:
    cursor_x: int
    word: str
    style: Styling


@dataclass(kw_only=True)
class Command:
    left: int
    top: float
    bottom: float | None = None

    def execute(self, _scroll, _canvas):
        pass


@dataclass
class DrawText(Command):
    text: str
    font: tkinter.font.Font
    color: str

    def __post_init__(self):
        self.bottom = self.top + self.font.metrics("linespace")

    def execute(self, scroll, canvas: tkinter.Canvas):
        canvas.create_text(
            self.left,
            self.top - scroll,
            text=self.text,
            font=self.font,
            anchor="nw",
            fill=self.color,
        )


@dataclass
class DrawRect(Command):
    right: int
    color: str

    def execute(self, scroll, canvas):
        canvas.create_rectangle(
            self.left,
            self.top - scroll,
            self.right,
            self.bottom - scroll,
            width=0,
            fill=self.color,
        )


class DocumentLayout:
    def __init__(self, node, width: int):
        self.node = node
        self.parent = None
        self.children = []

        self.x = HSTEP
        self.y = VSTEP
        self.width = width - 2 * HSTEP
        self.height = None

    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        child.layout()
        self.height = child.height

    def paint(self) -> List[Command]:
        return []


LayoutMode = Enum("LayoutMode", ["INLINE", "BLOCK"])
BLOCK_ELEMENTS = [
    "html",
    "body",
    "article",
    "section",
    "nav",
    "aside",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hgroup",
    "header",
    "footer",
    "address",
    "p",
    "hr",
    "pre",
    "blockquote",
    "ol",
    "ul",
    "menu",
    "li",
    "dl",
    "dt",
    "dd",
    "figure",
    "figcaption",
    "main",
    "div",
    "table",
    "form",
    "fieldset",
    "legend",
    "details",
    "summary",
]


class BlockLayout(object):
    def __init__(
        self,
        node: Node,
        parent: "DocumentLayout | BlockLayout",
        previous: "BlockLayout | None",
    ):
        self.line: List[LineUnit] = []
        self.display_list: List[Command] = []

        self.x: int | None = None
        self.y: int | None = None
        self.width = None
        self.height = None

        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

    def _is_pre(self) -> bool:
        return isinstance(self.node, Element) and self.node.tag == "pre"

    def _is_abbr(self, parent) -> bool:
        return isinstance(parent, Element) and parent.tag == "abbr"

    def _is_sup(self, parent) -> bool:
        return isinstance(parent, Element) and parent.tag == "sup"

    def _is_bold(self, parent) -> bool:
        return isinstance(parent, Element) and parent.tag == "b"

    def _is_italic(self, parent) -> bool:
        return isinstance(parent, Element) and parent.tag == "i"

    def paint(self) -> List[Command]:
        cmds = []
        if isinstance(self.node, Element):
            bgcolor = self.node.style.get("background-color", "transparent")
            if bgcolor != "transparent":
                x2, y2 = self.x + self.width, self.y + self.height
                rect = DrawRect(
                    left=self.x, top=self.y, right=x2, bottom=y2, color=bgcolor
                )
                cmds.append(rect)
        if self.layout_mode() == LayoutMode.INLINE:
            for command in self.display_list:
                cmds.append(command)

        return cmds

    def layout(self):
        mode = self.layout_mode()
        self.x = self.parent.x
        self.width = self.parent.width

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        if mode == LayoutMode.BLOCK:
            # Reads from HTML tree and writes to the layout tree.
            previous = None
            for child in self.node.children:
                next = BlockLayout(child, self, previous)
                self.children.append(next)
                previous = next
        else:
            self.cursor_x = 0
            self.cursor_y = 0
            self.recurse(self.node)
            self.flush()

        for child in self.children:
            child.layout()

        if mode == LayoutMode.BLOCK:
            self.height = sum([child.height for child in self.children])
        else:
            self.height = self.cursor_y

    def layout_mode(self) -> LayoutMode:
        if isinstance(self.node, Text):
            return LayoutMode.INLINE
        elif any(
            [
                isinstance(child, Element) and child.tag in BLOCK_ELEMENTS
                for child in self.node.children
            ]
        ):
            return LayoutMode.BLOCK
        elif self.node.children:
            return LayoutMode.INLINE
        else:
            return LayoutMode.BLOCK

    def recurse(self, node: Node):
        if isinstance(node, Text) and self._is_pre():
            line = ""
            for c in node.text:
                if c == "\n":
                    self._handle_text(node, line)
                    self.flush()
                    line = ""
                else:
                    line += c
            if len(line) != 0:
                self._handle_text(node, line)
        elif isinstance(node, Text):
            for word in node.text.split():
                self._handle_text(node, word)
        else:
            # XXX: assumes everything in this branch is an Element
            assert isinstance(node, Element)
            if node.tag == "br":
                self.flush()

            for child in node.children:
                self.recurse(child)

    def _handle_text(self, node: Node, word: str):
        if not self._is_overflowing(node, word) or SOFT_HYPHEN not in word:
            self.word(node, word)
            return

        # too long and contains a soft hyphen, try to split word on hyphen
        hyph_idx = self._find_longest_hyph(node, word)
        hyph_idx_inclusive = hyph_idx + 1
        for sub in (word[:hyph_idx_inclusive], word[hyph_idx_inclusive:]):
            if sub:
                self.word(node, sub)

    def _find_longest_hyph(self, node: Node, word: str) -> int:
        hyph_idx = len(word)
        while SOFT_HYPHEN in word:
            if not self._is_overflowing(node, word):
                break
            hyph_idx = word.rindex(SOFT_HYPHEN)
            word = word[:hyph_idx]
        return hyph_idx

    def word(self, node: Node, word: str):
        if self._is_overflowing(node, word):
            self.flush()

        if self._is_abbr(node.parent):
            word = word.upper()

        font = self._get_font(node)
        word_len = font.measure(word)
        color = node.style["color"]
        style = Styling(font, color)
        if self._is_sup(node.parent):
            style.valignment = "Top"
        self.line.append(LineUnit(self.cursor_x, word, style))
        if not self._is_pre():
            self.cursor_x += word_len + font.measure(" ")
        else:
            self.cursor_x += word_len

    def _is_overflowing(self, node: Node, word: str) -> bool:
        font = self._get_font(node)
        word_len = font.measure(word)
        return self.cursor_x + word_len > self.width

    def _get_font(self, node: Node):
        if self._is_pre():
            family = "Courier New"
        else:
            family = node.style["font-family"]

        if self._is_bold(node.parent) or self._is_abbr(node.parent):
            weight = "bold"
        else:
            weight = node.style["font-weight"]

        if self._is_italic(node.parent):
            slant = "italic"
        else:
            slant = node.style["font-style"]

        if slant == "normal":
            slant = "roman"

        size = int(float(node.style["font-size"][:-2]) * 0.75)
        if self._is_sup(node.parent):
            size = math.ceil(size / 2)

        font = get_font(
            family,
            size,
            weight.casefold() == WEIGHT_BOLD,
            slant == SLANT_ITALIC,
        )

        return font

    def flush(self):
        if not self.line:
            return
        metrics = [lu.style.font.metrics() for lu in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent

        for lu in self.line:
            x = self.x + lu.cursor_x
            y = self.y + baseline - lu.style.font.metrics("ascent")
            if lu.style.valignment == "Top":
                y = self.y + baseline - max_ascent
            self.display_list.append(
                DrawText(
                    left=x,
                    top=y,
                    text=lu.word,
                    font=lu.style.font,
                    color=lu.style.color,
                )
            )
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = 0
        self.line = []


FONTS = {}


def get_font(family: str, size: int, is_bold: bool, is_italic: bool):
    weight = WEIGHT_BOLD if is_bold else WEIGHT_NORMAL
    slant = SLANT_ITALIC if is_italic else SLANT_ROMAN
    key = (family, size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(family=family, size=size, weight=weight, slant=slant)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]


def paint_tree(layout: DocumentLayout | BlockLayout, display_list):
    display_list.extend(layout.paint())
    for child in layout.children:
        paint_tree(child, display_list)
