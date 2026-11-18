import pytest
from bol_is import bol

def test_bol():
    assert bol(10, 2) == 5.0
    assert bol(1, 0) is None
    assert bol(-6, 3) == -2.0
