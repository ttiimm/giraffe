from giraffe.browser import DisplayUnit, layout

LOREM_IPSUM = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore 
et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo 
consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. 
Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."""


def test_layout():
    display_list = layout("hi mom")
    assert [
        DisplayUnit(13 * 1, 18, "h"),
        DisplayUnit(13 * 2, 18, "i"),
        DisplayUnit(13 * 3, 18, " "),
        DisplayUnit(13 * 4, 18, "m"),
        DisplayUnit(13 * 5, 18, "o"),
        DisplayUnit(13 * 6, 18, "m"),
    ] == display_list


def test_layout_wraps():
    display_list = layout(LOREM_IPSUM)
    assert display_list[0] == DisplayUnit(13, 18, "L")
    assert display_list[-1] == DisplayUnit(364, 144, ".")

