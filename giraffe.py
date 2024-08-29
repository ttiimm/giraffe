import tkinter
import tkinter.font

from giraffe.browser import Browser

if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        Browser().new_tab(sys.argv[1])
        tkinter.mainloop()
    else:
        print("usage: giraffe <url>")
        sys.exit(1)
