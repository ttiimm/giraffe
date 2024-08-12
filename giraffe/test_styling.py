import pytest
from giraffe.styling import CSSParser, ParseError

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
