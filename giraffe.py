import tkinter

from giraffe.browser import Browser
from giraffe.net import URL


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        Browser().load(URL(sys.argv[1]))
        tkinter.mainloop()
    else:
        print("usage: giraffe <url>")
        sys.exit(1)
