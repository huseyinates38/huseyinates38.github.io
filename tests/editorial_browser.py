#!/usr/bin/env python3
"""Run existing rendered regressions and mark the current editorial release."""
from pathlib import Path
import json,runpy
ROOT=Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT/'tests/browser_smoke.py'),run_name='__main__')
report=json.loads((ROOT/'browser-report.json').read_text());report['release']='3.2'
(ROOT/'browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
quality=json.loads((ROOT/'_site/quality-report.json').read_text());quality['browser_checks']=report
(ROOT/'_site/quality-report.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2))
print('Rendered regression report is attached to editorial release 3.2.')
