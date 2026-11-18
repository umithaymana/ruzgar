# Created by Ümit & Gökçenur — Dilim gercek_paket
from paket_is import isle, normalize

def test_normalize():
    assert normalize('  AbC ') == 'abc'

def test_isle():
    assert isle(['Merhaba', 'x', 'MERHABA'], 'merhaba') == ['Merhaba', 'MERHABA']
    assert isle([], 'a') == []
