from dataclasses import dataclass
import tkinter.font
from typing import List, Sequence


@dataclass
class Text:
    text: str


@dataclass
class Tag:
    tag: str


def lex(body: str, is_viewsource=False) -> List[Text | Tag]:
    if is_viewsource:
        return [Text(body)]

    out = []
    buffer = ""
    in_tag = False
    consume = 0

    for i, c in enumerate(body):
        if consume:
            consume -= 1
            continue

        if c == "<":
            in_tag = True
            if buffer:
                out.append(Text(buffer))
            buffer = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(buffer))
            buffer = ""
        elif c == "&" and body[i : i + 4] == "&lt;":
            buffer += "<"
            consume += 3
        elif c == "&" and body[i : i + 4] == "&gt;":
            buffer += ">"
            consume += 3
        else:
            buffer += c
    if not in_tag and buffer:
        out.append(Text(buffer))
    return out


HSTEP, VSTEP = 13, 18


WEIGHT_NORMAL = "normal"
WEIGHT_BOLD = "bold"
SLANT_ROMAN = "roman"
SLANT_ITALIC = "italic"


@dataclass
class DisplayUnit:
    cursor_x: int
    cursor_y: float
    word: str
    font: tkinter.font.Font


class Layout(object):
    def __init__(self, tokens: Sequence[Text | Tag], width: int):
        self.display_list = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.is_bold = False
        self.is_italic = False
        self.width = width

        for tok in tokens:
            self.token(tok)

    def token(self, tok):
        if isinstance(tok, Text):
            for word in tok.text.split():
                self.word(word)
        elif tok.tag == "i":
            self.is_italic = True
        elif tok.tag == "/i":
            self.is_italic = False
        elif tok.tag == "b":
            self.is_bold = True
        elif tok.tag == "/b":
            self.is_bold = False

    def word(self, word):
        font = tkinter.font.Font(
            family="Iosevka",
            size=16,
            weight=WEIGHT_BOLD if self.is_bold else WEIGHT_NORMAL,
            slant=SLANT_ITALIC if self.is_italic else SLANT_ROMAN,
        )
        w = font.measure(word)
        if self.cursor_x + w > self.width - HSTEP:
            self.cursor_y += lineheight(font)
            self.cursor_x = HSTEP
        self.display_list.append(DisplayUnit(self.cursor_x, self.cursor_y, word, font))
        self.cursor_x += w + font.measure(" ")


def lineheight(font):
    return font.metrics("linespace") * 1.25
