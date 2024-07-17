from giraffe.browser import WIDTH, DisplayUnit, HSTEP, VSTEP, layout

LOREM_IPSUM = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore 
et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo 
consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. 
Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."""


def test_layout():
    display_list = layout("hi mom", WIDTH)
    assert [
        DisplayUnit(HSTEP * 1, VSTEP, "h"),
        DisplayUnit(HSTEP * 2, VSTEP, "i"),
        DisplayUnit(HSTEP * 3, VSTEP, " "),
        DisplayUnit(HSTEP * 4, VSTEP, "m"),
        DisplayUnit(HSTEP * 5, VSTEP, "o"),
        DisplayUnit(HSTEP * 6, VSTEP, "m"),
    ] == display_list


def test_layout_wraps():
    display_list = layout(LOREM_IPSUM, WIDTH)
    assert display_list[0] == DisplayUnit(HSTEP, VSTEP, "L")
    assert display_list[-1] == DisplayUnit(650, 216, ".")


def test_layout_newlines():
    display_list = layout("hello\nworld", WIDTH)
    assert display_list[4] == DisplayUnit(HSTEP * 5, VSTEP, "o")
    assert display_list[5] == DisplayUnit(HSTEP * 1, VSTEP * 3, "w")

# XXX: re-visit this with more examples?
def test_layout_skip_consecutive():
    display_list = layout("hello\n\nworld", WIDTH)
    assert display_list[4] == DisplayUnit(HSTEP * 5, VSTEP, "o")
    assert display_list[5] == DisplayUnit(HSTEP * 1, VSTEP * 3, "w")