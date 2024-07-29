from dataclasses import dataclass, field
from typing import Dict, List, Self

"""The lexing and parsing code used by the browser.

This code is based on Chapter 4 of 
[Web Browser Engineering](https://browser.engineering/html.html).
"""

SOFT_HYPHEN = "\N{SOFT HYPHEN}"

SELF_CLOSING_TAGS = (
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
)
HEAD_TAGS = (
    "base",
    "basefont",
    "bgsound",
    "noscript",
    "link",
    "meta",
    "title",
    "style",
    "script",
)


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
    attributes: Dict[str, str] = field(default_factory=dict)

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
    def __init__(self, body: str, do_implicit=True):
        self.body = body
        self.unfinished = []
        self.do_implicit = do_implicit

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
        self.implicit_tags(None)
        parent = self.unfinished[-1]
        node = Text(text, parent=parent)
        parent.children.append(node)

    def add_tag(self, tag: str):
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"):
            return

        self.implicit_tags(tag)

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
        if not self.unfinished:
            self.implicit_tags(None)
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()

    def implicit_tags(self, tag):
        while True and self.do_implicit:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                if tag in HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif open_tags == ["html", "head"] and tag not in ("/head",) + HEAD_TAGS:
                self.add_tag("/head")
            else:
                break


def print_tree(node: Node, indent=0):
    print(" " * indent, str(node))
    for child in node.children:
        print_tree(child, indent + 2)