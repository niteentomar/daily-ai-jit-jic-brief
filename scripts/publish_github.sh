#!/bin/bash
# CL-075: publish the code to GitHub (owner runs from Terminal; uses your own git/gh login).
#   ./scripts/publish_github.sh [repo-name] [--public]
# Steps: 1) re-index so .gitignore applies (drops tracked slides/pptx/plist from the index; files stay on disk)
#        2) secret scan of every file that would be committed - aborts on any hit
#        3) commit  4) create the GitHub repo with gh (private unless --public) or push to an existing origin
set -e
cd "$(dirname "$0")/.."
NAME="${1:-daily-ai-jit-jic-brief}"; VIS="--private"; [ "$2" = "--public" ] && VIS="--public"
rm -f .git/index.lock 2>/dev/null || true
git rm -r -q --cached -f . >/dev/null
git add -A
echo "== files to publish: $(git diff --cached --name-only --diff-filter=ACMR | wc -l | tr -d ' ') added/changed"
LEAK=$(git diff --cached --name-only --diff-filter=ACMR -z | xargs -0 grep -nIE \
  "(SG\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}|AIza[0-9A-Za-z_-]{30,}|tvly-[A-Za-z0-9-]{20,}|-----BEGIN (RSA |EC )?PRIVATE KEY|\"private_key\"|sk-[A-Za-z0-9]{32,}|lsv2_[A-Za-z0-9_]{20,})" 2>/dev/null \
  | grep -vE "tvly-test-key|AIzaSyTest|AIzaSyFAKE" || true)
if [ -n "$LEAK" ]; then echo "SECRET SCAN FAILED - nothing committed:"; echo "$LEAK" | cut -c1-120; git reset -q; exit 1; fi
BAD=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '(^|/)\.env$|^_backups/|^_to_delete/|\.db$|\.pptx$' || true)
if [ -n "$BAD" ]; then echo "BLOCKED (must never be published):"; echo "$BAD"; git reset -q; exit 1; fi
echo "== secret scan clean"
MSG="v2 production: Argon pipeline, dedup v2, paper scoring, scheduler + watchdog (CL-061..CL-075)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01MqpPpkY9od9YwyianyPmti"
if git remote get-url origin >/dev/null 2>&1; then
  git commit -q -m "$MSG"
else
  # First publish: one clean commit with NO parent, so earlier local history (old PPT, slide images,
  # plist) is never uploaded. Local history stays in the reflog; working files are untouched.
  C=$(git commit-tree "$(git write-tree)" -m "$MSG")
  git update-ref "refs/heads/$(git branch --show-current)" "$C"
fi
echo "== committed $(git rev-parse --short HEAD) ($(git rev-list --count HEAD) commit(s) on this branch)"
BR=$(git branch --show-current)
if git remote get-url origin >/dev/null 2>&1; then
  git push -u origin "$BR"
elif command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
  gh repo create "$NAME" $VIS --source . --remote origin --push --description "Autonomous daily AI briefing: JIT news, JIC concepts and a lesson, built test-first"
else
  echo "No origin and gh not logged in. Either run: gh auth login   (then re-run this script)"
  echo "or create an empty repo named $NAME on github.com and run:"
  echo "  git remote add origin https://github.com/<you>/$NAME.git && git push -u origin $BR"
fi
