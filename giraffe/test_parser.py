from giraffe.parser import HtmlParser

"""Test cases for the browser's HTML parser.

These test help verify the content and exercises for Chapter 4 of
[Web Browser Engineering](https://browser.engineering/html.html).
"""


def test_parse():
    content = "<html>hi</html>"
    dom = HtmlParser(content, do_implicit=False).parse()
    assert str(dom) == "<html>hi</html>"


def test_parse_with_entities():
    dom = HtmlParser("<html>&lt;div&gt;</html>", do_implicit=False).parse()
    assert str(dom) == "<html><div></html>"


def test_parse_with_doctype():
    dom = HtmlParser("<!doctype html><html>hi</html>", do_implicit=False).parse()
    assert str(dom) == "<html>hi</html>"


def test_parse_ignores_ws():
    dom = HtmlParser("<!doctype html>\n<html>hi</html>", do_implicit=False).parse()
    assert str(dom) == "<html>hi</html>"


def test_parse_ignores_comment():
    dom = HtmlParser(
        "<html><!-- ignore me please -->hi</html>", do_implicit=False
    ).parse()
    assert str(dom) == "<html>hi</html>"


def test_parse_with_comment_start():
    dom = HtmlParser("<html><!-->hi</html>", do_implicit=False).parse()
    assert str(dom) == "<html>hi</html>"


def test_sibling_paragraphs():
    dom = HtmlParser("<body><p>hello</p><p>world</p>", do_implicit=False).parse()
    assert len(dom.children) == 2
    assert str(dom.children[0]) == "<p>hello</p>"
    assert str(dom.children[1]) == "<p>world</p>"


def test_sibling_paragraphs_unfinished():
    dom = HtmlParser("<body><p>hello<p>world</p>", do_implicit=False).parse()
    assert len(dom.children) == 2
    assert str(dom.children[0]) == "<p>hello</p>"
    assert str(dom.children[1]) == "<p>world</p>"


def test_sibling_divs_finished():
    dom = HtmlParser(
        "<body><div>hello</div><div>world</div>", do_implicit=False
    ).parse()
    assert len(dom.children) == 2
    assert str(dom.children[0]) == "<div>hello</div>"
    assert str(dom.children[1]) == "<div>world</div>"


def test_sibling_divs_unfinished():
    dom = HtmlParser("<body><div>hello<div>world</div>", do_implicit=False).parse()
    assert len(dom.children) == 1
    assert str(dom.children[0]) == "<div>hello<div>world</div></div>"


def test_parse_with_void_tag():
    dom = HtmlParser("<html><br>hi</html>", do_implicit=False).parse()
    assert str(dom) == "<html><br>hi</html>"


def test_parse_with_attributes():
    dom = HtmlParser('<html><div id="main">hi</div></html>', do_implicit=False).parse()
    assert str(dom) == '<html><div id="main" >hi</div></html>'


def test_parse_with_implicit_html():
    dom = HtmlParser('<head></head><body><div id="main">hi</div></body>').parse()
    assert str(dom) == '<html><head></head><body><div id="main" >hi</div></body></html>'


def test_parse_with_implicit_head():
    dom = HtmlParser("<html><meta></html").parse()
    assert str(dom) == "<html><head><meta></head></html>"


def test_parse_with_implicit_head_no_headers():
    dom = HtmlParser('<html><body><div id="main">hi</div></body></html').parse()
    assert str(dom) == '<html><body><div id="main" >hi</div></body></html>'


def test_parse_with_implicit_body():
    dom = HtmlParser('<html><head></head><div id="main">hi</div></html').parse()
    assert str(dom) == '<html><head></head><body><div id="main" >hi</div></body></html>'


def test_parse_when_viewsource():
    dom = HtmlParser("<html>hi</html>", do_implicit=False).parse(is_viewsource=True)
    assert str(dom) == "<view-source><html>hi</html></view-source>"


def test_parse_with_emoji():
    content = """<html><head><meta charset="utf-8"></head><body>
        &#9924; <!-- Snowman emoji -->
        &#128512; <!-- Smiley face emoji -->
        ⛄
        😀
    </body></html>
    """
    # FIXME: handle emoji when encoded
    dom = HtmlParser(content).parse()
    assert "⛄" in str(dom)
    assert "😀" in str(dom)


def test_parse_unclosed_tag():
    content = "Hi!<hr"
    dom = HtmlParser(content).parse()
    assert str(dom) == "<html><body>Hi!</body></html>"


def test_parse_soft_hyphe():
    content = "<body>Hi&shy;!</body>"
    dom = HtmlParser(content, do_implicit=False).parse()
    assert str(dom) == "<body>Hi\N{SOFT HYPHEN}!</body>"
