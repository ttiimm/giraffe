from dataclasses import dataclass, field
from typing import Dict, List, Self, TypeVar

"""The lexing and parsing code used by the browser.

This code is based on Chapter 4 of 
[Web Browser Engineering](https://browser.engineering/html.html).
"""

SOFT_HYPHEN = "\N{SOFT HYPHEN}"
DOUBLE_QUOTE = '"'
SINGLE_QUOTE = "'"

WS = ("\n", "\r", "\t")

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
SIBLING_TAGS = (
    "p",
    "li",
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
    parent: "Element | None" = None
    children: List["Text | Element"] = field(default_factory=list)


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
        self.unfinished: List[Element] = []
        self.do_implicit = do_implicit

    def parse(self, is_viewsource=False) -> Node:
        if is_viewsource:
            self.add_tag("view-source")
            self.add_text(self.body)
            self.add_tag("/view-source")
            return self.finish()

        buffer = ""
        # XXX: probably state machine would help here
        in_tag = False
        in_script = False
        in_attribute = False
        in_double = False
        in_single = False
        consume = 0

        for i, c in enumerate(self.body):
            if consume:
                consume -= 1
                continue

            if c == DOUBLE_QUOTE and in_tag and not in_double:
                in_double = True
                in_attribute = True
                buffer += c
            elif c == DOUBLE_QUOTE and in_double:
                in_attribute = False
                in_double = False
                buffer += c
            elif c == SINGLE_QUOTE and in_tag and not in_single:
                in_attribute = True
                in_single = True
                buffer += c
            elif c == SINGLE_QUOTE and in_single:
                in_attribute = False
                in_single = False
                buffer += c
            elif c == "<" and not in_script and not in_attribute:
                in_tag = True
                if buffer:
                    self.add_text(buffer)
                buffer = ""
            elif c == "<" and in_script and self.body[i : i + 9] == "</script>":
                in_tag = True
                in_script = False
                if buffer:
                    self.add_text(buffer)
                buffer = ""
            elif c == ">" and not in_script and not in_attribute:
                in_tag = False
                if buffer == "script":
                    in_script = True
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

        if tag.startswith("/") and tag[1:] in SIBLING_TAGS:
            if len(self.unfinished) == 1:
                return
            node = self.unfinished[-1]
            siblings = []
            while node.tag == self.unfinished[-1].tag:
                siblings.append(self.unfinished.pop())
            node = siblings[-1]
            parent = self.unfinished[-1]
            parent.children.append(node)
            if len(siblings) > 1:
                for s in siblings[:-1]:
                    self.unfinished.append(s)
        elif tag.startswith("/"):
            if len(self.unfinished) == 1:
                return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent=parent)
            parent.children.append(node)
        elif tag in SIBLING_TAGS:
            parent = self.unfinished[-1] if self.unfinished else None
            if parent is not None and parent.tag == tag:
                parent = parent.parent
            node = Element(tag, attributes, parent=parent)
            self.unfinished.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent=parent)
            self.unfinished.append(node)
            if tag == "script":
                self.in_script = True

    def get_attributes(self, text: str):
        parts = text.split(" ")
        tag = parts[0].casefold()

        buffer = ""
        key = ""
        in_value = False
        in_single = False
        in_double = False

        attributes = {}

        for c in text[len(tag) :]:
            if c == " " and not in_value and buffer:
                attributes[buffer.casefold()] = ""
                buffer = ""
            elif c in WS and not in_value and not in_single and not in_double:
                continue
            elif (c == " " or c in WS) and (in_single or in_double):
                buffer += c
            elif c == " " and in_value and not in_single and not in_double:
                attributes[key.casefold()] = buffer
                buffer = ""
                key = ""
                in_value = False
            elif c == "=" and not in_value:
                key = buffer
                buffer = ""
                in_value = True
            elif c == SINGLE_QUOTE and in_value and not in_single:
                in_single = True
            elif c == SINGLE_QUOTE and in_value and in_single:
                in_single = False
            elif c == DOUBLE_QUOTE and in_value and not in_double:
                in_double = True
            elif c == DOUBLE_QUOTE and in_value and in_double:
                in_double = False
            elif c == ' ':
                continue
            else:
                buffer += c
        
        if not in_value and buffer:
            attributes[buffer.casefold()] = ''
        elif in_value and buffer:
            attributes[key.casefold()] = buffer

        # tag = parts[0].casefold()
        # attributes = {}
        # for attrpair in parts[1:]:
        #     if "=" in attrpair:
        #         key, value = attrpair.split("=", 1)
        #         if len(value) > 2 and value[0] in (SINGLE_QUOTE, DOUBLE_QUOTE):
        #             value = value[1:-1]
        #         attributes[key.casefold()] = value
        #     else:
        #         attributes[attrpair.casefold()] = ""
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
