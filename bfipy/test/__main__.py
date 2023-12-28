"""
    bfipy/test/__main__.py

    run all defined unit tests
"""


from unittest import main as utmain

from bfipy.test.interpreter import (
    TestBFI
)


if __name__ == '__main__':
    # run all imported TestCases
    utmain(verbosity=2)
