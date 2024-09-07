from dataclasses import dataclass
from typing import List

from giraffe.parser import INHERITED_PROPERTIES, Element, Node

"""A parser for CSS used in web pages.

This code is based on Chapter 6 of
[Web Browser Engineering](https://browser.engineering/styles.html).
"""


class ParseError(Exception):
    def __init__(self, error: str, position: int | None = None):
        super().__init__(error)
        self.error = error
        self.position = position

    def __str__(self):
        if self.position is not None:
            return f"{self.error} at position {self.position}"
        return self.error


@dataclass
class Rule:
    selector: "TagSelector | DescendantSelector"
    body: dict[str, str]

    def cascade_priority(self):
        return self.selector.priority


class CSSParser:
    def __init__(self, s: str, strict=False):
        self.s = s
        self.i = 0
        self.strict = strict

    def parse(self) -> List[Rule]:
        rules = []
        while self.i < len(self.s):
            try:
                self.whitespace()
                selector = self.selector()
                self.literal("{")
                self.whitespace()
                body = self.body()
                self.whitespace()
                self.literal("}")
                rules.append(Rule(selector, body))
            except ParseError as e:
                if self.strict:
                    raise e
                why = self.ignore_until(["}"])
                if why == "}":
                    self.literal("}")
                    self.whitespace()
                else:
                    break
        return rules

    def selector(self):
        out = TagSelector(self.word().casefold())
        self.whitespace()
        while self.i < len(self.s) and self.s[self.i] != "{":
            tag = self.word()
            descendant = TagSelector(tag.casefold())
            out = DescendantSelector(out, descendant)
            self.whitespace()
        return out

    def body(self) -> dict[str, str]:
        pairs = {}
        while self.i < len(self.s) and self.s[self.i] != "}":
            try:
                prop, val = self.pair()
                pairs[prop.casefold()] = val
                self.whitespace()
                self.literal(";")
                self.whitespace()
            except ParseError as e:
                if self.strict:
                    raise e
                else:
                    why = self.ignore_until([";", "}"])
                    if why == ";":
                        self.literal(";")
                        self.whitespace()
                    else:
                        break
        return pairs

    def pair(self):
        prop = self.word()
        self.whitespace()
        self.literal(":")
        self.whitespace()
        val = self.word()
        return prop.casefold(), val

    def word(self):
        start = self.i
        while self.i < len(self.s):
            if self.s[self.i].isalnum() or self.s[self.i] in "#-.%":
                self.i += 1
            else:
                break
        if not (self.i > start):
            raise ParseError("Parsing error", self.i)
        return self.s[start : self.i]

    def ignore_until(self, chars):
        while self.i < len(self.s):
            if self.s[self.i] in chars:
                return self.s[self.i]
            else:
                self.i += 1
        return None

    def literal(self, literal):
        if not (self.i < len(self.s) and self.s[self.i] == literal):
            raise ParseError("Literal not found", self.i)
        self.i += 1

    def whitespace(self):
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1


class TagSelector:
    def __init__(self, tag):
        self.tag = tag
        self.priority = 1

    def matches(self, node: Node):
        return isinstance(node, Element) and self.tag == node.tag

    def __repr__(self) -> str:
        return f"TagSelector({self.tag})"

    def __eq__(self, other):
        if isinstance(other, TagSelector):
            return self.tag == other.tag
        return False

    def __hash__(self):
        return hash(self.tag)


class DescendantSelector:
    def __init__(
        self, ancestor: "DescendantSelector | TagSelector", descendant: TagSelector
    ):
        self.ancestor = ancestor
        self.descendant = descendant
        self.priority = ancestor.priority + descendant.priority

    def matches(self, node):
        if not self.descendant.matches(node):
            return False
        while node.parent:
            if self.ancestor.matches(node.parent):
                return True
            node = node.parent
        return False


DEFAULT_STYLE_SHEET = CSSParser(open("browser.css").read()).parse()


def style(node: Node, rules: "None | List[Rule]" = None):
    if rules is None:
        rules = DEFAULT_STYLE_SHEET.copy()

    for property, default_value in INHERITED_PROPERTIES.items():
        if node.parent:
            node.style[property] = node.parent.style[property]
        else:
            node.style[property] = default_value

    for rule in rules:
        if not rule.selector.matches(node):
            continue
        for property, value in rule.body.items():
            node.style[property] = value

    if isinstance(node, Element) and "style" in node.attributes:
        pairs = CSSParser(node.attributes["style"]).body()
        for property, value in pairs.items():
            node.style[property] = value

    if node.style["font-size"].endswith("%"):
        if node.parent:
            parent_font_size = node.parent.style["font-size"]
        else:
            parent_font_size = INHERITED_PROPERTIES["font-size"]
        node_pct = float(node.style["font-size"][:-1]) / 100
        parent_px = float(parent_font_size[:-2])
        node.style["font-size"] = str(node_pct * parent_px) + "px"

    if isinstance(node, Element):
        name = node.tag
    else:
        name = node.text
    # print(f"{str(name)} -> {node.style}")
    # print("")

    for child in node.children:
        style(child, rules)
