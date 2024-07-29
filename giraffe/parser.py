from dataclasses import dataclass, field
from typing import Dict, List, Self

"""The lexing and parsing code used by the browser.

This code is based on Chapter 4 of 
[Web Browser Engineering](https://browser.engineering/html.html).
"""

SOFT_HYPHEN = "\N{SOFT HYPHEN}"

SELF_CLOSING_TAGS = [
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
]


@dataclass(kw_only=True)
class Node:
    parent: Self | None = None
    children: List["Node"] = field(default_factory=list)


@dataclass
class Text(Node):
    text: str

    def __str__(self) -> str:
        return self.text


@dataclass
class Element(Node):
    tag: str
    attributes: Dict[str, str]

    def __str__(self) -> str:
        child_strs = ""
        for c in self.children:
            child_strs += str(c)

        if self.attributes:
            attrs = " "
        else:
            attrs = ""
        for key in self.attributes.keys():
            attrs += f'{key}="{self.attributes[key]}" '

        if self.tag in SELF_CLOSING_TAGS:
            close_tag = ""
        else:
            close_tag = f"</{self.tag}>"
        return f"<{self.tag}{attrs}>{child_strs}{close_tag}"


class HtmlParser:
    def __init__(self, body: str):
        self.body = body
        self.unfinished = []

    def parse(self, is_viewsource=False) -> Node:
        if is_viewsource:
            self.add_tag("view-source")
            self.add_text(self.body)
            self.add_tag("/view-source")
            return self.finish()

        buffer = ""
        in_tag = False
        consume = 0

        for i, c in enumerate(self.body):
            if consume:
                consume -= 1
                continue

            if c == "<":
                in_tag = True
                if buffer:
                    self.add_text(buffer)
                buffer = ""
            elif c == ">":
                in_tag = False
                self.add_tag(buffer)
                buffer = ""
            elif c == "&" and self.body[i : i + 4] == "&lt;":
                buffer += "<"
                consume += 3
            elif c == "&" and self.body[i : i + 4] == "&gt;":
                buffer += ">"
                consume += 3
            elif c == "&" and self.body[i : i + 5] == "&shy;":
                buffer += SOFT_HYPHEN
                consume += 4
            else:
                buffer += c
        if not in_tag and buffer:
            self.add_text(buffer)
        return self.finish()

    def add_text(self, text: str):
        if text.isspace():
            return
        parent = self.unfinished[-1]
        node = Text(text, parent=parent)
        parent.children.append(node)

    def add_tag(self, tag: str):
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"):
            return

        if tag.startswith("/"):
            if len(self.unfinished) == 1:
                return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent=parent)
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent=parent)
            self.unfinished.append(node)

    def get_attributes(self, text: str):
        parts = text.split()
        tag = parts[0].casefold()
        attributes = {}
        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                if len(value) > 2 and value[0] in ["'", '"']:
                    value = value[1:-1]
                attributes[key.casefold()] = value
            else:
                attributes[attrpair.casefold()] = ""
        return tag, attributes

    def finish(self):
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()


def print_tree(node: Node, indent=0):
    print(" " * indent, str(node))
    for child in node.children:
        print_tree(child, indent + 2)
