#!/usr/bin/env python3
"""Herkese açık Türkçe akademik CV: verified public records only.

Keep in sync with English public CV; do not treat pending or unsuccessful
applications as grants. No unpublished manuscripts or private correspondence.
"""
from pathlib import Path
import json
import build_professional_docs as docs
ROOT = Path(__file__).resolve().parents[1]


def main():
    data=json.loads((ROOT/'content/cv-tr.json').read_text(encoding='utf-8'))
    assert len(data)==3
    docs.OUT.mkdir(parents=True,exist_ok=True)
    docs.fonts()
    docs.export_document('Huseyin_Ates_Akademik_Ozgecmis_TR',data,'Hüseyin Ateş — Akademik Özgeçmiş',lang='tr')
    print('Turkish public CV: three sections generated as PDF and DOCX')

if __name__ == '__main__': main()
