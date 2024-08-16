import tkinter
from typing import List

import pytest

from giraffe.layout import DocumentLayout
from giraffe.parser import Node, Element, Text
from giraffe.styling import INHERITED_PROPERTIES


"""Test cases for the browser's layout engine.

These test help verify the content and exercises for Chapter 3 of
[Web Browser Engineering](https://browser.engineering/text.html).
"""


WIDTH = 800

LOREM_IPSUM = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore 
et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo 
consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. 
Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."""

APOLLINAIRE = Text("""
        L          TE
          A       A
            C    V
             R A
             DOU
             LOU
            REUSE
            QUE TU
            PORTES
          ET QUI T'
          ORNE O CI
           VILISÃ‰
          OTE-  TU VEUX
           LA    BIEN
          SI      RESPI
                  RER       - Apollinaire
""")


@pytest.fixture(scope="session")
def _setup_tkinter():
    tkinter.Tk()
    yield
    pass


def test_layout(_setup_tkinter):
    nodes = Text("hi mom")
    root = DocumentLayout(nodes, WIDTH)
    root.layout()
    display_list = root.children[0].display_list
    assert display_list[0].text == "hi"
    assert display_list[1].text == "mom"
    assert display_list[0].top == display_list[1].top
    assert display_list[0].left < display_list[1].left


def test_layout_wraps(_setup_tkinter):
    nodes = Text(LOREM_IPSUM)
    root = DocumentLayout(nodes, WIDTH)
    root.layout()
    display_list = root.children[0].display_list
    assert display_list[0].text == "Lorem"
    assert display_list[-1].text == "laborum."
    assert display_list[0].top < display_list[-1].top


def test_sup(_setup_tkinter):
    width = 100
    sup_tag = Element("sup")
    nodes = treeify(Element("div"), [Text("hey"), sup_tag])
    treeify(sup_tag, Text("guy"))
    root = DocumentLayout(nodes, width)
    root.layout()
    display_list = root.children[0].display_list
    first, second = display_list[0], display_list[1]
    assert first.text == "hey"
    assert second.text == "guy"
    assert first.top == second.top
    assert first.font["size"] != second.font["size"]


def test_soft_hyphens(_setup_tkinter):
    width = 100
    nodes = Text("supercalifragilis\N{SOFT HYPHEN}ticexpialidocious")
    root = DocumentLayout(nodes, width)
    root.layout()
    display_list = root.children[0].display_list
    assert len(display_list) == 2
    assert display_list[0].text[-1] == "\N{SOFT HYPHEN}"
    assert display_list[0].top < display_list[1].top


def test_soft_hyphens_with_multiple(_setup_tkinter):
    width = 275
    nodes = Text("supercalifragilis\N{SOFT HYPHEN}ticexpialidociou\N{SOFT HYPHEN}s")
    root = DocumentLayout(nodes, width)
    root.layout()
    display_list = root.children[0].display_list
    assert len(display_list) == 2
    assert display_list[0].text[-1] == "\N{SOFT HYPHEN}"
    assert display_list[1].text == "s"
    assert display_list[0].top < display_list[1].top


def test_small_caps(_setup_tkinter):
    width = 100
    nodes = treeify(Element("abbr"), Text("like this"))
    root = DocumentLayout(nodes, width)
    root.layout()
    display_list = root.children[0].display_list
    first = display_list[0]
    second = display_list[1]
    font_conf = first.font.config() or {"weight": None}
    assert first.text == "LIKE"
    assert font_conf["weight"] == "bold"
    assert second.text == "THIS"
    font_conf = second.font.config() or {"weight": None}
    assert font_conf["weight"] == "bold"


def test_pre(_setup_tkinter):
    width = 100
    nodes = treeify(Element("pre"), APOLLINAIRE)
    root = DocumentLayout(nodes, width)
    root.layout()
    display_list = root.children[0].display_list
    assert len(display_list) == 17


def test_pre_bold(_setup_tkinter):
    width = 100
    b_tag = Element("b")
    nodes = treeify(Element("pre"), [Text("    hello"), b_tag])
    treeify(b_tag, Text("world"))
    root = DocumentLayout(nodes, width)
    root.layout()
    display_list = root.children[0].display_list
    assert display_list[0].text == "    hello"
    assert display_list[1].text == "world"
    font_conf = display_list[1].font.config() or {"weight": None}
    assert font_conf["weight"] == "bold"


def treeify(parent: Node, children: Node | List[Node]) -> Node:
    """Sets the parent/child relationships between a parent and children."""

    if not isinstance(children, List):
        children = [children]

    for child in children:
        parent.children.append(child)
        child.parent = parent
    return parent
