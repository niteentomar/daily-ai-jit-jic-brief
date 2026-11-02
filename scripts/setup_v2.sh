#!/bin/bash
# CL-061..066 go-live check. Creates an isolated .venv (system Python untouched),
# installs pinned requirements, runs the full test suite, and ONLY if every test
# passes runs one --dry-run (real API calls, no email, no pointer change).
# Output: logs/setup_v2.log
cd "$(dirname "$0")/.."
mkdir -p logs
exec > >(tee logs/setup_v2.log) 2>&1
echo "=== 1/3 create .venv and install requirements ==="
python3 -m venv .venv || exit 1
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt || { echo "INSTALL FAILED"; exit 1; }
.venv/bin/pip list 2>/dev/null | grep -iE "^(litellm|langchain|langchain-core|tavily-python|ddgs|streamlit) "
echo "=== 2/3 full test suite (gate: all must pass) ==="
.venv/bin/python -m pytest -q -p no:cacheprovider || { echo "TESTS FAILED - stopping before dry-run (TST-T-003)"; exit 1; }
echo "=== 3/3 dry-run (real APIs, no email) ==="
.venv/bin/python main.py --dry-run
echo "=== exit code $? ==="
