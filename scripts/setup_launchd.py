"""
MODULE: setup_launchd.py
PURPOSE: Generate and install the macOS launchd jobs (CL-075 production):
         - com.niteen.ai-aggregator          07:00 daily: main.py --scheduled
         - com.niteen.ai-aggregator.watchdog 09:30 daily: scripts/watchdog.py
         Both use the project .venv Python and the project as working directory.
         launchd runs a missed calendar job when the Mac wakes; pair with
         `pmset repeat wakeorpoweron` (scripts/install_production.sh) so the Mac wakes at 06:55.
INPUTS: project_root, python_path (defaults: this repo, .venv/bin/python)
OUTPUTS: two plists at project root; with --install, copies to ~/Library/LaunchAgents/
DEPENDENCIES: pathlib, shutil, sys (stdlib only)
RULE REFERENCES: GIT-H-001 (logs/ is gitignored), R-016 (schedule guards)
CHANGE LOG: 1.0.0 | 2026-06-17 | TC-009 initial implementation | Claude Code
            2.0.0 | 2026-11-02 | CL-075: --scheduled entry, .venv python, WorkingDirectory,
            watchdog job, --install flag | Claude Code
"""
import shutil
import sys
from pathlib import Path

_LABEL = "com.niteen.ai-aggregator"
_WATCHDOG_LABEL = f"{_LABEL}.watchdog"
_PLIST_NAME = f"{_LABEL}.plist"
_LAUNCH_AGENTS = Path.home() / "Library" / "LaunchAgents"

_PLIST_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{script}</string>{extra_arg}
    </array>
    <key>WorkingDirectory</key>
    <string>{root}</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{hour}</integer>
        <key>Minute</key>
        <integer>{minute}</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{stdout_log}</string>
    <key>StandardErrorPath</key>
    <string>{stderr_log}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
"""


def generate_plist(project_root: str, python_path: str, *, hour: int = 7, minute: int = 0) -> str:
    """Pipeline job XML (main.py --scheduled) with every path resolved."""
    root = Path(project_root)
    return _PLIST_TEMPLATE.format(label=_LABEL, python_path=python_path, script=str(root / "main.py"),
                                  extra_arg="\n        <string>--scheduled</string>", root=str(root),
                                  hour=hour, minute=minute,
                                  stdout_log=str(root / "logs" / "launchd_stdout.log"),
                                  stderr_log=str(root / "logs" / "launchd_stderr.log"))


def generate_watchdog_plist(project_root: str, python_path: str, *, hour: int = 9, minute: int = 30) -> str:
    """Watchdog job XML (scripts/watchdog.py)."""
    root = Path(project_root)
    return _PLIST_TEMPLATE.format(label=_WATCHDOG_LABEL, python_path=python_path,
                                  script=str(root / "scripts" / "watchdog.py"), extra_arg="", root=str(root),
                                  hour=hour, minute=minute,
                                  stdout_log=str(root / "logs" / "watchdog_stdout.log"),
                                  stderr_log=str(root / "logs" / "watchdog_stderr.log"))


def write_plists(project_root: str, python_path: str) -> list:
    root = Path(project_root)
    out = []
    for name, xml in ((_PLIST_NAME, generate_plist(project_root, python_path)),
                      (f"{_WATCHDOG_LABEL}.plist", generate_watchdog_plist(project_root, python_path))):
        (root / name).write_text(xml, encoding="utf-8")
        out.append(root / name)
        print(f"Wrote: {root / name}")
    return out


def install(paths: list) -> list:
    _LAUNCH_AGENTS.mkdir(parents=True, exist_ok=True)
    dests = []
    for src in paths:
        dest = _LAUNCH_AGENTS / src.name
        shutil.copy2(src, dest)
        dests.append(dest)
        print(f"Installed: {dest}")
    return dests


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    venv_py = project_root / ".venv" / "bin" / "python"
    paths = write_plists(str(project_root), str(venv_py if venv_py.exists() else sys.executable))
    if "--install" in sys.argv:
        install(paths)
