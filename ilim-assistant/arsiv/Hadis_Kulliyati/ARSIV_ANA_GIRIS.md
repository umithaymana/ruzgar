# Hadis_Kulliyati — Ümit & Gökçenur

Kutüb-i Sitte’nin **birincil Arapça matınları** knowledge raftında tutulur:

`knowledge/ilim/din/05_hadis/kutub_i_sitte/{buhari,muslim,ebu_davud,tirmizi,nesai,ibn_mace}/`

İncegest: `python scripts/faz5_hadis_kutub_sitte_ingest.py`

Bu klasör ek PDF/TXT (şerh, müsned, ekstra mecmua) için staging alanıdır. RAG: `python -m ilim_assistant.ingest_cli --incremental` (knowledge `*.md`) veya `python -m ilim_assistant.arsiv_indexle` (arsiv).

**Alt klasörler (öneri):** `Kutub_i_Sitte`, `Diger_Hadis_Kaynaklari`
