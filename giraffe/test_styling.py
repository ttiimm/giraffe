import pytest
from giraffe.parser import Element, Text
from giraffe.styling import (
    CSSParser,
    DescendantSelector,
    ParseError,
    Rule,
    TagSelector,
    style,
)

"""Test cases for the browser's CSS parser.

These test help verify the content and exercises for Chapter 6 of
[Web Browser Engineering](https://browser.engineering/styles.html).
"""


def test_whitespace():
    parser = CSSParser(" ")
    parser.whitespace()
    # TODO assertion?


def test_word():
    parser = CSSParser("background-color:lightblue")
    word = parser.word()
    assert word == "background-color"


def test_word_when_missing():
    parser = CSSParser("   ")
    with pytest.raises(ParseError):
        parser.word()


def test_literal():
    parser = CSSParser(":")
    parser.literal(":")
    # TODO assertion?


def test_literal_when_missing():
    parser = CSSParser(" ")
    with pytest.raises(ParseError):
        parser.literal(":")


def test_pair():
    parser = CSSParser("background-color:lightblue")
    assert parser.pair() == ("background-color", "lightblue")


def test_pair_with_whitespace():
    parser = CSSParser("background-color : lightblue")
    assert parser.pair() == ("background-color", "lightblue")


def test_body():
    parser = CSSParser("background-color:lightblue; padding: .5rem;")
    assert parser.body() == {"background-color": "lightblue", "padding": ".5rem"}


def test_body_when_strict():
    parser = CSSParser("background-color:lightblue; hi", strict=True)
    with pytest.raises(ParseError):
        parser.body()


def test_body_when_not_strict():
    parser = CSSParser("background-color:lightblue; hi", strict=False)
    assert parser.body() == {"background-color": "lightblue"}


def test_style_with_text():
    text = Text("hi")
    style(text)
    assert text


def test_style_with_element():
    el = Element("div", attributes={"style": "background-color:lightblue;"})
    style(el)
    assert "background-color" in el.style


def test_style_with_element_children():
    parent = Element("body")
    el = Element("div", attributes={"style": "background-color:lightblue;"})
    el.parent = parent
    parent.children.append(el)
    style(parent)
    assert "background-color" in el.style


def test_tag_selector_matches():
    selector = TagSelector("div")
    div = Element("div")
    assert selector.matches(div)


def test_tag_selector_no_match():
    selector = TagSelector("div")
    p = Element("p")
    assert not selector.matches(p)


def test_descendant_selector_matches():
    ancestor = TagSelector("body")
    descendant = TagSelector("div")
    selector = DescendantSelector(ancestor, descendant)

    parent = Element("body")
    el = Element("div", attributes={"style": "background-color:lightblue;"})
    el.parent = parent
    parent.children.append(el)
    assert selector.matches(el)


def test_descendant_selector_no_match():
    ancestor = TagSelector("body")
    descendant = TagSelector("div")
    selector = DescendantSelector(ancestor, descendant)

    parent = Element("body")
    el = Element("p", attributes={"style": "background-color:lightblue;"})
    el.parent = parent
    parent.children.append(el)
    assert not selector.matches(el)


def test_descendant_selector_with_grandparent():
    ancestor = TagSelector("body")
    descendant = TagSelector("p")
    selector = DescendantSelector(ancestor, descendant)

    grandparent = Element("body")
    div = Element("div")
    div.parent = grandparent
    grandparent.children.append(div)
    el = Element("p", attributes={"style": "background-color:lightblue;"})
    el.parent = div
    div.children.append(el)
    assert selector.matches(el)


def test_parse():
    book_css = """
        html { font-size: 24px; line-height: 1.3; padding: 0.5ex; }
        pre { font-size: 18px; overflow: auto; padding-left: 2ex; }
    """
    rules = CSSParser(book_css).parse()
    assert len(rules) == 2


def test_parse_nested_selector():
    book_css = """
       pre {
        font-size: 18px;
        overflow: auto;
        padding-left: 2ex;
        }
        
        @media print {
            pre { font-size: 10px; }
        }
    """
    rules = CSSParser(book_css).parse()
    assert len(rules) == 1


def test_parse_full_book_css():
    with open("data/book.css") as f:
        rules = CSSParser(f.read()).parse()
        pre_only = [r for r in rules if isinstance(r.selector, TagSelector) and r.selector.tag == "pre"]
        assert len(pre_only) == 1