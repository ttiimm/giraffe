from dataclasses import dataclass
from typing import List

"""The lexing and parsing code used by the browser.

This code is based on Chapter 4 of 
[Web Browser Engineering](https://browser.engineering/html.html).
"""

SOFT_HYPHEN = "\N{SOFT HYPHEN}"


class Node:
    def __init__(self, parent):
        self.parent = parent
        self.children = []


@dataclass
class Text(Node):
    text: str


@dataclass
class Element(Node):
    tag: str


def lex(body: str, is_viewsource=False) -> List[Text | Element]:
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
            out.append(Element(buffer))
            buffer = ""
        elif c == "&" and body[i : i + 4] == "&lt;":
            buffer += "<"
            consume += 3
        elif c == "&" and body[i : i + 4] == "&gt;":
            buffer += ">"
            consume += 3
        elif c == "&" and body[i : i + 5] == "&shy;":
            buffer += SOFT_HYPHEN
            consume += 4
        else:
            buffer += c
    if not in_tag and buffer:
        out.append(Text(buffer))
    return out
