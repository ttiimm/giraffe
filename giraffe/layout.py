import math
import tkinter.font
from dataclasses import dataclass
from enum import Enum
from typing import List, Literal

from giraffe.parser import SOFT_HYPHEN, Element, Node, Text

"""The layout code used by the browser.

This code is based on Chapter 3/5/7 of 
[Web Browser Engineering](https://browser.engineering/).
"""


HSTEP, VSTEP = 13, 18

TAG_TEXT = "gText"

WEIGHT_NORMAL = "normal"
WEIGHT_BOLD = "bold"
SLANT_ROMAN = "roman"
SLANT_ITALIC = "italic"


@dataclass
class Rect:
    left: int
    top: int
    right: int
    bottom: int

    def contains_point(self, x, y):
        return x >= self.left and x < self.right and y >= self.top and y < self.bottom


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


class DrawOutline:
    def __init__(self, rect, color, thickness):
        self.rect = rect
        self.color = color
        self.thickness = thickness

    def execute(self, scroll, canvas):
        canvas.create_rectangle(
            self.rect.left,
            self.rect.top - scroll,
            self.rect.right,
            self.rect.bottom - scroll,
            width=self.thickness,
            outline=self.color,
        )


class DrawLine:
    def __init__(self, x1, y1, x2, y2, color, thickness):
        self.rect = Rect(x1, y1, x2, y2)
        self.color = color
        self.thickness = thickness

    def execute(self, scroll, canvas):
        canvas.create_line(
            self.rect.left,
            self.rect.top - scroll,
            self.rect.right,
            self.rect.bottom - scroll,
            fill=self.color,
            width=self.thickness,
        )


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
            tags=TAG_TEXT
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
        self.children: "List[BlockLayout]" = []

        self.x = HSTEP
        self.y = VSTEP
        self.width = width - 2 * HSTEP
        self.height = 0

    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        child.layout()
        self.height = child.height

    def paint(self) -> List[Command]:
        return []


class LineLayout:
    def __init__(
        self,
        node: Node,
        parent: "BlockLayout",
        previous: "LineLayout | None",
    ):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children: List[TextLayout] = []

    def layout(self):
        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        for word in self.children:
            word.layout()

        # XXX: handle the case where there aren't children better
        if not self.children:
            self.height = 0
        else:
            max_ascent = max([word.font.metrics("ascent") for word in self.children])
            baseline = self.y + 1.25 * max_ascent

            for word in self.children:
                word.y = baseline - word.font.metrics("ascent")
            max_descent = max([word.font.metrics("descent") for word in self.children])
            self.height = 1.25 * (max_ascent + max_descent)

    def paint(self):
        return []


class TextLayout:
    def __init__(
        self,
        node: Node,
        word: str,
        parent: LineLayout,
        previous: "TextLayout | None",
    ):
        self.node = node
        self.word = word
        self.children = []
        self.parent = parent
        self.previous = previous
        self.x: "int | None" = None
        self.y: "int | None" = None
        self.font: "tkinter.font.Font | None" = None

    def layout(self):
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        size = int(float(self.node.style["font-size"][:-2]) * 0.75)
        if is_sup(self.node.parent):
            size = math.ceil(size / 2)

        family = self.node.style["font-family"]
        self.font = get_font(
            family, size, weight.casefold() == WEIGHT_BOLD, style != "normal"
        )

        self.width = self.font.measure(self.word)
        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x
        self.height = self.font.metrics("linespace")

    def paint(self):
        color = self.node.style["color"]
        return [
            DrawText(
                left=self.x,
                top=self.y,
                text=self.word,
                font=self.font,
                color=color,
            )
        ]


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
        self.x: int | None = None
        self.y: int | None = None
        self.width = None
        self.height = None

        self.node = node
        self.parent = parent
        self.previous = previous
        self.children: List["LineLayout | BlockLayout"] = []

    def _is_pre(self) -> bool:
        return isinstance(self.node, Element) and self.node.tag == "pre"

    def _is_abbr(self, parent) -> bool:
        return isinstance(parent, Element) and parent.tag == "abbr"

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
            self.new_line()
            self.recurse(self.node)

        for child in self.children:
            child.layout()

        self.height = sum([child.height for child in self.children])

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
                    self.new_line()
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
                self.new_line()

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
            self.new_line()
        line = self.children[-1]
        previous_word = line.children[-1] if line.children else None
        text = TextLayout(node, word, line, previous_word)
        line.children.append(text)

        if self._is_abbr(node.parent):
            word = word.upper()

        font = self._get_font(node)
        word_len = font.measure(word)
        color = node.style["color"]
        style = Styling(font, color)
        if is_sup(node.parent):
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
        if is_sup(node.parent):
            size = math.ceil(size / 2)

        font = get_font(
            family,
            size,
            weight.casefold() == WEIGHT_BOLD,
            slant == SLANT_ITALIC,
        )

        return font

    def new_line(self):
        self.cursor_x = 0
        last_line = self.children[-1] if self.children else None
        new_line = LineLayout(self.node, self, last_line)
        self.children.append(new_line)

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


def is_sup(parent: Node) -> bool:
    return isinstance(parent, Element) and parent.tag == "sup"


FONTS = {}


def get_font(
    family: str, size: int, is_bold: bool, is_italic: bool
) -> tkinter.font.Font:
    weight = WEIGHT_BOLD if is_bold else WEIGHT_NORMAL
    slant = SLANT_ITALIC if is_italic else SLANT_ROMAN
    key = (family, size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(family=family, size=size, weight=weight, slant=slant)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]


def paint_tree(
    layout: DocumentLayout | BlockLayout | LineLayout | TextLayout, display_list
):
    display_list.extend(layout.paint())
    for child in layout.children:
        paint_tree(child, display_list)
