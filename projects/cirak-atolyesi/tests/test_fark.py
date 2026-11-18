from fark_is import fark

def test_fark_pozitif():
    assert fark(9, 4) == 5

def test_fark_negatif():
    assert fark(3, 10) == -7
