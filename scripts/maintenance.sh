#!/bin/bash
# =============================================================
# MAINTENANCE COMMANDS — Daily JIT/JIC AI Newsletter System
# Run from project root:
#   cd "<project-root>"
# =============================================================

# --- 1. START STREAMLIT DASHBOARD ---
start_dashboard() {
    echo "Starting Streamlit dashboard on http://localhost:8501 ..."
    lsof -ti:8501 | xargs kill -9 2>/dev/null || true
    python3 -m streamlit run frontend/app.py --server.port 8501
}

# --- 2. STOP STREAMLIT ---
stop_dashboard() {
    echo "Stopping Streamlit on port 8501 ..."
    lsof -ti:8501 | xargs kill -9 2>/dev/null && echo "Stopped." || echo "Nothing running on 8501."
}

# --- 3. RUN PIPELINE MANUALLY ---
run_pipeline() {
    echo "Running daily pipeline ..."
    python3 main.py
}

# --- 4. CHECK ENVIRONMENT ---
check_env() {
    python3 scripts/check_env.py
}

# --- 5. RUN TESTS ---
run_tests() {
    python3 -m pytest tests/ -v 2>&1 | tail -10
}

# --- 6. RESET TOPIC POINTER ---
reset_pointer() {
    python3 -c "
import json
with open('config/topic_pool.json', 'r') as f:
    data = json.load(f)
data['pointer'] = 0
with open('config/topic_pool.json', 'w') as f:
    json.dump(data, f, indent=2)
print('Pointer reset to 0 — next topic:', data['topics'][0])
"
}

# --- 7. CLEAR DATABASE (DEMO RESET ONLY — bypasses R-004) ---
reset_database() {
    python3 -c "
import sqlite3
conn = sqlite3.connect('database/ledger.db')
conn.execute('DROP TRIGGER IF EXISTS prevent_delete_historical_ledger')
conn.execute('DELETE FROM historical_ledger')
conn.execute('DELETE FROM gateway_telemetry_logs')
conn.execute('DELETE FROM system_exceptions')
conn.execute(\"DELETE FROM sqlite_sequence WHERE name IN ('historical_ledger','gateway_telemetry_logs','system_exceptions')\")
conn.execute('''CREATE TRIGGER prevent_delete_historical_ledger
BEFORE DELETE ON historical_ledger
BEGIN
    SELECT RAISE(ABORT, \'DELETE on historical_ledger is forbidden: R-004 append-only rule\');
END''')
conn.commit()
conn.close()
print('Database cleared and trigger restored.')
"
}

# --- 8. CHECK LAUNCHD SCHEDULER STATUS ---
# NOTE (CL-026): logs/launchd_stderr.log is append-only and has never been
# cleared. As of 2026-06-22 it holds 4 tracebacks: the first 3 are stale,
# pre-CL-024 ".env" FileNotFoundError failures (already fixed). Fresh
# failures start at traceback #4 onward — check timestamps/line numbers in
# the traceback against the current source before assuming a logged error
# is still live. Consider truncating this log after confirming a fix lands.
check_scheduler() {
    echo "=== launchd status ==="
    launchctl list | grep niteen
    echo "=== last stderr log ==="
    tail -20 logs/launchd_stderr.log
}

# --- 9. VIEW LAST RUN LOG ---
view_logs() {
    tail -50 logs/launchd_stderr.log
}

# --- 10. REINSTALL DEPENDENCIES ---
reinstall_deps() {
    pip3 install -r requirements.txt --upgrade
}

# --- USAGE ---
echo "Available functions:"
echo "  start_dashboard   — launch Streamlit on localhost:8501"
echo "  stop_dashboard    — kill Streamlit"
echo "  run_pipeline      — run main.py manually"
echo "  check_env         — validate .env"
echo "  run_tests         — run pytest suite"
echo "  reset_pointer     — reset topic queue to index 0"
echo "  reset_database    — clear all ledger data (demo reset only)"
echo "  check_scheduler   — show launchd status + last stderr"
echo "  view_logs         — tail last 50 lines of launchd log"
echo "  reinstall_deps    — pip install -r requirements.txt --upgrade"
echo ""
echo "Usage: source scripts/maintenance.sh then call the function"
echo "   OR: bash scripts/maintenance.sh (shows this menu only)"
