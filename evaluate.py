"""Run the accuracy checks:  python evaluate.py"""
import json
from pathlib import Path

from resq.dataset import CSV_PATH, write_csv
from resq.evaluation import run_checks
from resq.model import Brain
from resq.pipeline import Analyzer

if not Path(CSV_PATH).exists():
    write_csv()

brain = Brain(CSV_PATH)
result = run_checks(brain, Analyzer(brain))
misses = result.pop("misses")
confusion = result.pop("confusion_matrix", None)

print("RESQ-AI evaluation (synthetic demo data, small check set)")
print("-" * 60)
for k, v in result.items():
    print(f"{k:38s} {v}")
if confusion:
    types = confusion["types"]
    print("\nConfusion matrix (rows = actual, columns = predicted):")
    print(" " * 16 + "".join(t[:6].ljust(8) for t in types))
    for t in types:
        row = confusion["matrix"][t]
        print(t.ljust(16) + "".join(str(row[p]).ljust(8) for p in types))
if misses:
    print("\nCheck-set sentences the system got wrong:")
    for m in misses:
        print(f" - {m['report']}\n     expected {m['expected']}  got {m['got']}")
