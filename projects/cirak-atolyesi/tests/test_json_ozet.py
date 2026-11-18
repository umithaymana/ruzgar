from json_ozet import json_ozet

def test_json_ozet():
    veri = {"b": 2, "a": 1}
    res = json_ozet(veri)
    assert '"a": 1' in res
    assert '"b": 2' in res
