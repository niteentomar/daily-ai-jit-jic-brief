#!/bin/bash
# CL-075 production install (macOS). Run once from Terminal:
#   ./scripts/install_production.sh            (asks for your Mac password once, for the wake schedule)
# 1. sets SCHEDULE_END_DATE in .env (default: 15 runs starting tomorrow) if not set
# 2. writes + installs two launchd jobs: pipeline 07:00 (main.py --scheduled), watchdog 09:30
# 3. wakes the Mac daily at 06:55 (pmset; needs power adapter on most Macs)
# Undo: ./scripts/install_production.sh --uninstall
cd "$(dirname "$0")/.."
LA="$HOME/Library/LaunchAgents"; U=$(id -u)
JOBS="com.niteen.ai-aggregator com.niteen.ai-aggregator.watchdog"
if [ "$1" = "--uninstall" ]; then
  for j in $JOBS; do launchctl bootout gui/$U "$LA/$j.plist" 2>/dev/null; done
  sudo pmset repeat cancel; echo "Scheduler and wake schedule removed (plists left in $LA)."; exit 0
fi
[ -x .venv/bin/python ] || { echo "Missing .venv - run ./scripts/setup_v2.sh first"; exit 1; }
if ! grep -q "^SCHEDULE_END_DATE=" .env; then
  END=$(date -v+15d +%Y-%m-%d)
  printf "\n# CL-075 production window (15 daily runs from tomorrow)\nSCHEDULE_END_DATE=%s\n" "$END" >> .env
fi
echo "Schedule ends: $(grep '^SCHEDULE_END_DATE=' .env | cut -d= -f2)"
.venv/bin/python scripts/setup_launchd.py --install || exit 1
for j in $JOBS; do
  launchctl bootout gui/$U "$LA/$j.plist" 2>/dev/null
  launchctl bootstrap gui/$U "$LA/$j.plist" && echo "Loaded $j"
done
echo "Setting daily wake at 06:55 (password needed):"
sudo pmset repeat wakeorpoweron MTWRFSU 06:55:00
echo "--- status ---"; launchctl list | grep ai-aggregator; pmset -g sched | head -5
echo "Done. First run: tomorrow 07:00. Watchdog: 09:30. Logs: logs/launchd_*.log, logs/watchdog/"
