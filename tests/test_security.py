"""
MODULE: test_security.py
PURPOSE: Test cases for scripts/check_env.py secret-scanning utility
INPUTS: Real project files (T-SEC-S-001/S-002), pytest tmp_path (T-SEC-N-001)
OUTPUTS: Pass/fail assertions per TEST_REGISTRY T-SEC-* acceptance criteria
DEPENDENCIES: pytest, pathlib, scripts.check_env
RULE REFERENCES: SEC-X-001, SEC-X-002, SEC-X-003, ZT-001
CHANGE LOG: 1.0.0 | 2026-06-16 | TC-001 initial tests (T-SEC-S-001, S-002, N-001) | Claude Code
"""
from pathlib import Path

from scripts import check_env

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# scripts/check_env.py defines the secret patterns themselves, so its own source
# necessarily contains the literal pattern strings (e.g. "api_key ="). Excluded
# from the scan as a known-safe exception — see docs/plans/PLAN_TC001_repo_init.md
# Decision 3. Mirrors real-world scanner convention (gitleaks, trufflehog exclude
# their own rule-definition files).
SCANNER_SELF_EXCLUSION = {PROJECT_ROOT / "scripts" / "check_env.py"}


def _project_files_to_scan():
    candidates = [
        PROJECT_ROOT / ".env.example",
        PROJECT_ROOT / ".gitignore",
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "requirements.txt",
        PROJECT_ROOT / "scripts" / "setup_db.py",
        PROJECT_ROOT / "tests" / "conftest.py",
        PROJECT_ROOT / "tests" / "test_env.py",
        PROJECT_ROOT / "tests" / "test_security.py",
    ]
    return [p for p in candidates if p.exists() and p not in SCANNER_SELF_EXCLUSION]


def test_t_sec_s_001_no_secrets_in_committed_files():
    """T-SEC-S-001: scan returns zero matches across all TC-001 project files."""
    findings = check_env.scan_for_secrets(_project_files_to_scan())
    assert findings == []


def test_t_sec_s_002_env_in_gitignore():
    """T-SEC-S-002: .gitignore contains a line that is exactly '.env'."""
    gitignore_lines = (PROJECT_ROOT / ".gitignore").read_text().splitlines()
    assert gitignore_lines.count(".env") >= 1


def test_t_sec_n_001_scanner_detects_planted_secret(tmp_path):
    """T-SEC-N-001 (negative): scanner flags a deliberately planted fake secret,
    proving the detector is not a no-op."""
    fake_secret_file = tmp_path / "leaky_module.py"
    fake_secret_file.write_text('api_key = "AIzaSyFAKEPLANTEDSECRETFORTESTONLY"\n')
    findings = check_env.scan_for_secrets([fake_secret_file])
    assert len(findings) >= 1
    assert any(f["file"] == str(fake_secret_file) for f in findings)
