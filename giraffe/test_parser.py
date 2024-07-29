from giraffe.parser import HtmlParser, print_tree

"""Test cases for the browser's HTML parser.

These test help verify the content and exercises for Chapter 4 of
[Web Browser Engineering](https://browser.engineering/html.html).
"""


def test_parse():
    content = "<html>hi</html>"
    dom = HtmlParser(content).parse()
    assert str(dom) == "<html>hi</html>"


def test_parse_with_entities():
    dom = HtmlParser("<html>&lt;div&gt;</html>").parse()
    assert str(dom) == "<html><div></html>"


def test_parse_with_doctype():
    dom = HtmlParser("<!doctype html><html>hi</html>").parse()
    assert str(dom) == "<html>hi</html>"


def test_parse_ignores_ws():
    dom = HtmlParser("<!doctype html>\n<html>hi</html>").parse()
    assert str(dom) == "<html>hi</html>"


def test_parse_with_void_tag():
    dom = HtmlParser("<html><br>hi</html>").parse()
    assert str(dom) == "<html><br>hi</html>"


def test_parse_with_attributes():
    dom = HtmlParser('<html><div id="main">hi</div></html>').parse()
    assert str(dom) == '<html><div id="main" >hi</div></html>'


# def test_lext_when_viewsource():
#     content = "<html>hi</html>"
#     assert lex(content, is_viewsource=True) == [Text("<html>hi</html>")]


# def test_lex_with_emoji():
#     content = """<html><head><meta charset="utf-8"></head><body>
#         &#9924; <!-- Snowman emoji -->
#         &#128512; <!-- Smiley face emoji -->
#         ⛄
#         😀
#     </body></html>
#     """
#     # FIXME: handle emoji when encoded
#     tokens = lex(content)
#     assert tokens[9] == Text("\n        ⛄ \n        😀\n    ")


# def test_lex_unclosed_tag():
#     content = "Hi!<hr"
#     assert lex(content) == [Text("Hi!")]


# def test_lex_soft_hyphe():
#     content = "Hi&shy;!"
#     assert lex(content) == [Text("Hi\N{SOFT HYPHEN}!")]
