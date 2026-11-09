#!/usr/bin/env bash
# Mac / Linux launcher:  ./run.sh
cd "$(dirname "$0")"
PY=python3
command -v python3 >/dev/null 2>&1 || PY=python
if ! $PY -c "import pandas, sklearn" >/dev/null 2>&1; then
  echo "First run: installing pandas and scikit-learn (needs internet once)..."
  $PY -m pip install -r requirements.txt || { echo "Install failed."; exit 1; }
fi
$PY server.py
