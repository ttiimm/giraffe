"""A parser for CSS used in web pages.

This code is based on Chapter 6 of
[Web Browser Engineering](https://browser.engineering/styles.html).
"""

from giraffe.parser import Element, Node


class ParseError(Exception):
    def __init__(self, error: str, position: int | None = None):
        super().__init__(error)
        self.error = error
        self.position = position

    def __str__(self):
        if self.position is not None:
            return f"{self.error} at position {self.position}"
        return self.error


class CSSParser:
    def __init__(self, s: str, strict=False):
        self.s = s
        self.i = 0
        self.strict = strict
    
    def parse(self):
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
                rules.append((selector, body))
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

    def body(self):
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

    def matches(self, node: Node):
        return isinstance(node, Element) and self.tag == node.tag


class DescendantSelector:
    def __init__(
        self, ancestor: "DescendantSelector | TagSelector", descendant: TagSelector
    ):
        self.ancestor = ancestor
        self.descendant = descendant

    def matches(self, node):
        if not self.descendant.matches(node):
            return False
        while node.parent:
            if self.ancestor.matches(node.parent):
                return True
        return False


def style(node: Node):
    if isinstance(node, Element) and "style" in node.attributes:
        pairs = CSSParser(node.attributes["style"]).body()
        for property, value in pairs.items():
            node.style[property] = value
    for child in node.children:
        style(child)
