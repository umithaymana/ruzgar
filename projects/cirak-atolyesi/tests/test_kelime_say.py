from kelime_say import kelime_say

def test_kelime_say():
    assert kelime_say("merhaba dünya") == 2
    assert kelime_say("") == 0
    assert kelime_say(None) == 0
