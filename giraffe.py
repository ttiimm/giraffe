import tkinter
import tkinter.font

from giraffe.browser import Browser

if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        # TODO Get rid of displaying hyperlinks (?)
        Browser().load(sys.argv[1])
        tkinter.mainloop()
    else:
        print("usage: giraffe <url>")
        sys.exit(1)
