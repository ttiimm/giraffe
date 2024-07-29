import tkinter

import pytest

from giraffe.layout import Layout, Element, Text


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
    tokens = [Text("hi mom")]
    display_list = Layout(tokens, WIDTH).display_list
    assert display_list[0].word == "hi"
    assert display_list[1].word == "mom"
    assert display_list[0].cursor_y == 21.5
    assert display_list[1].cursor_y == 21.5
    assert display_list[0].cursor_x < display_list[1].cursor_x


def test_layout_wraps(_setup_tkinter):
    tokens = [Text(LOREM_IPSUM)]
    display_list = Layout(tokens, WIDTH).display_list
    assert display_list[0].word == "Lorem"
    assert display_list[-1].word == "laborum."
    assert display_list[0].cursor_y < display_list[-1].cursor_y


def test_center(_setup_tkinter):
    width = 100
    tokens = [Element('h1 class="title"'), Text("hi"), Element("/h1")]
    display_list = Layout(tokens, width).display_list
    first = display_list[0]
    assert first.word == "hi"
    assert first.cursor_x == 48


def test_sup(_setup_tkinter):
    width = 100
    tokens = [Text("hey"), Element("sup"), Text("guy"), Element("/sup")]
    display_list = Layout(tokens, width).display_list
    first, second = display_list[0], display_list[1]
    assert first.word == "hey"
    assert second.word == "guy"
    assert first.cursor_y == second.cursor_y
    assert first.font["size"] != second.font["size"]


def test_soft_hyphens(_setup_tkinter):
    width = 100
    tokens = [Text("supercalifragilis\N{SOFT HYPHEN}ticexpialidocious")]
    display_list = Layout(tokens, width).display_list
    assert len(display_list) == 2
    assert display_list[0].word[-1] == "\N{SOFT HYPHEN}"
    assert display_list[0].cursor_y < display_list[1].cursor_y


def test_soft_hyphens_with_multiple(_setup_tkinter):
    width = 233
    tokens = [Text("supercalifragilis\N{SOFT HYPHEN}ticexpialidociou\N{SOFT HYPHEN}s")]
    display_list = Layout(tokens, width).display_list
    assert len(display_list) == 2
    assert display_list[0].word[-1] == "\N{SOFT HYPHEN}"
    assert display_list[1].word == "s"
    assert display_list[0].cursor_y < display_list[1].cursor_y


def test_small_caps(_setup_tkinter):
    width = 100
    tokens = [Element("abbr"), Text("like this"), Element("/abbr")]
    display_list = Layout(tokens, width).display_list
    first = display_list[0]
    second = display_list[1]
    font_conf = first.font.config() or {"weight": None}
    assert first.word == "LIKE"
    assert font_conf["weight"] == "bold"
    assert second.word == "THIS"
    font_conf = second.font.config() or {"weight": None}
    assert font_conf["weight"] == "bold"


def test_preformated(_setup_tkinter):
    width = 100
    tokens = [Element("pre"), APOLLINAIRE, Element("/pre")]
    display_list = Layout(tokens, width).display_list
    assert len(display_list) == 17


# def test_preformated_bold(_setup_tkinter):
#     width = 100
#     tokens = lex("""<pre>
#     hello 
#     <b>world</b>
# </pre>""")
#     assert tokens == [
#         Element("pre"),
#         Text("\n    hello \n    "),
#         Element("b"),
#         Text("world"),
#         Element("/b"),
#         Text("\n"),
#         Element("/pre"),
#     ]
#     display_list = Layout(tokens, width).display_list
#     assert display_list[1].word == "    hello "
#     assert display_list[2].word == "    "
#     assert display_list[3].word == "world"
#     font_conf = display_list[3].font.config() or {"weight": None}
#     assert font_conf["weight"] == "bold"
