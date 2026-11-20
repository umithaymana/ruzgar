# -*- coding: utf-8 -*-
"""Türkçe sorgu ↔ Arapça Şamile chunk köprüsü (canlı MISS önleme)."""

from ilim_assistant.ruzgar_anlam_koruma import chunk_fits_query


def test_niyet_matches_arabic_niyyat():
    arabic = "إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى"
    assert chunk_fits_query("niyet hadisi", arabic)


def test_hadisi_token_bridges_to_hadith():
    arabic = "حَدَّثَنَا الْحُمَيْدِيُّ قَالَ حَدَّثَنَا سُفْيَانُ عَنْ يَحْيَى"
    assert chunk_fits_query("hadisi nedir", arabic)


def test_hicret_matches_hijra():
    arabic = "كانت الهجرة إلى المدينة في السنة الثالثة عشرة"
    assert chunk_fits_query("hicreti anlat", arabic)
