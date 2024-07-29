import math
import tkinter.font
from dataclasses import dataclass
from typing import List, Literal, Sequence

from giraffe.parser import SOFT_HYPHEN, Text, Element

"""The layout code used by the browser.

This code is based on Chapter 3 of 
[Web Browser Engineering](https://browser.engineering/text.html).
"""


HSTEP, VSTEP = 13, 18

WEIGHT_NORMAL = "normal"
WEIGHT_BOLD = "bold"
SLANT_ROMAN = "roman"
SLANT_ITALIC = "italic"


@dataclass
class Styling:
    font: tkinter.font.Font
    valignment: Literal["None", "Top"] = "None"


@dataclass
class LineUnit:
    cursor_x: int
    word: str
    style: Styling


@dataclass
class DisplayUnit:
    cursor_x: int
    cursor_y: float
    word: str
    font: tkinter.font.Font


class Layout(object):
    def __init__(self, tokens: Sequence[Text | Element], width: int):
        self.line: List[LineUnit] = []
        self.display_list: List[DisplayUnit] = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.is_bold = False
        self.is_italic = False
        self.is_centering = False
        self.is_sup = False
        self.is_abbr = False
        self.is_pre = False
        self.family: str | None = None
        self.width = width
        self.size = 14

        for tok in tokens:
            self.token(tok)
        self.flush()

    def token(self, tok):
        if isinstance(tok, Text) and self.is_pre:
            line = ""
            for c in tok.text:
                if c == "\n":
                    self._handle_word(line)
                    self.flush()
                    line = ""
                else:
                    line += c
            if len(line) != 0:
                self._handle_word(line)

        elif isinstance(tok, Text):
            for word in tok.text.split():
                self._handle_word(word)
        elif tok.tag == "i":
            self.is_italic = True
        elif tok.tag == "/i":
            self.is_italic = False
        elif tok.tag == "b":
            self.is_bold = True
        elif tok.tag == "/b":
            self.is_bold = False
        elif tok.tag == "small":
            self.size -= 2
        elif tok.tag == "/small":
            self.size += 2
        elif tok.tag == "big":
            self.size += 2
        elif tok.tag == "/big":
            self.size -= 2
        elif tok.tag == "br":
            self.flush()
        elif tok.tag == "/p":
            self.flush()
            self.cursor_y += VSTEP
        elif tok.tag == 'h1 class="title"':
            self.flush()
            self.is_centering = True
        elif tok.tag == "/h1":
            self.flush()
            self.is_centering = False
        elif tok.tag == "sup":
            self.size = math.ceil(self.size / 2)
            self.is_sup = True
        elif tok.tag == "/sup":
            self.size = self.size * 2
            self.is_sup = False
        elif tok.tag == "abbr":
            self.size -= 4
            self.is_abbr = True
        elif tok.tag == "/abbr":
            self.size += 4
            self.is_abbr = False
        elif tok.tag == "pre":
            self.is_pre = True
            self.family = "Courier New"
        elif tok.tag == "/pre":
            self.is_pre = False
            self.family = None

    def _handle_word(self, word):
        if not self._is_overflowing(word) or SOFT_HYPHEN not in word:
            self.word(word)
            return

        # too long and contains a soft hyphen, try to split word on hyphen
        hyph_idx = self._find_longest_hyph(word)
        hyph_idx_inclusive = hyph_idx + 1
        for sub in (word[:hyph_idx_inclusive], word[hyph_idx_inclusive:]):
            if sub:
                self.word(sub)

    def _find_longest_hyph(self, word: str) -> int:
        hyph_idx = len(word)
        while SOFT_HYPHEN in word:
            if not self._is_overflowing(word):
                break
            hyph_idx = word.rindex(SOFT_HYPHEN)
            word = word[:hyph_idx]
        return hyph_idx

    def word(self, word: str):
        if self._is_overflowing(word):
            self.flush()

        if self.is_abbr:
            word = word.upper()

        font = get_font(
            self.family, self.size, self.is_bold or self.is_abbr, self.is_italic
        )
        word_len = font.measure(word)
        style = Styling(font)
        if self.is_sup:
            style.valignment = "Top"
        self.line.append(LineUnit(self.cursor_x, word, style))
        if not self.is_pre:
            self.cursor_x += word_len + font.measure(" ")
        else:
            self.cursor_x += word_len

    def _is_overflowing(self, word: str) -> bool:
        font = get_font(self.family, self.size, self.is_bold, self.is_italic)
        word_len = font.measure(word)
        return self.cursor_x + word_len > self.width - HSTEP

    def flush(self):
        if not self.line:
            return
        metrics = [lu.style.font.metrics() for lu in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        remaining = self.width - self.cursor_x  # assumes cursor_x is width of line
        centering_offset = math.floor(remaining / 2.0)

        for lu in self.line:
            x = lu.cursor_x
            if self.is_centering:
                x = lu.cursor_x + centering_offset
            y = baseline - lu.style.font.metrics("ascent")
            if lu.style.valignment == "Top":
                y = baseline - max_ascent
            self.display_list.append(DisplayUnit(x, y, lu.word, lu.style.font))
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = HSTEP
        self.line = []


def lineheight(font):
    return font.metrics("linespace") * 1.25


FONTS = {}


def get_font(family, size, is_bold, is_italic):
    weight = WEIGHT_BOLD if is_bold else WEIGHT_NORMAL
    slant = SLANT_ITALIC if is_italic else SLANT_ROMAN
    key = (family, size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(family=family, size=size, weight=weight, slant=slant)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]
