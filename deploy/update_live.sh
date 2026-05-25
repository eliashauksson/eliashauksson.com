#!/usr/bin/env bash

set -euo pipefail

SERVICE_NAME="eliashaukssoncom"
TARGET_BRANCH="master"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

section() {
  printf '\n== %s ==\n' "$1"
}

run() {
  printf '+ %s\n' "$*"
  "$@"
}

section "Project"
cd "$PROJECT_ROOT"
printf 'Project root: %s\n' "$PROJECT_ROOT"

if [[ ! -f "main.py" || ! -d "app" ]]; then
  echo "Error: project root detection failed; main.py or app/ not found." >&2
  exit 1
fi

section "Git Safety"
current_branch="$(git branch --show-current)"
current_commit="$(git log -1 --oneline)"
printf 'Current branch: %s\n' "$current_branch"
printf 'Current commit: %s\n' "$current_commit"

if [[ "$current_branch" != "$TARGET_BRANCH" ]]; then
  echo "Error: refusing to deploy from branch '$current_branch'. Expected '$TARGET_BRANCH'." >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Error: refusing to deploy with uncommitted local changes:" >&2
  git status --short >&2
  exit 1
fi

section "Pull"
run git pull origin "$TARGET_BRANCH"
printf 'Latest commit: %s\n' "$(git log -1 --oneline)"

section "Python Environment"
if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
  printf 'Using virtualenv: %s\n' "$PROJECT_ROOT/.venv"
else
  echo "Warning: .venv/bin/activate not found; using system python and pip."
fi

section "Dependencies"
run python -m pip install -r requirements.txt

section "Checks"
run python -m compileall app
printf '+ python -m json.tool translations/en.json > /dev/null\n'
python -m json.tool translations/en.json > /dev/null
printf '+ python -m json.tool translations/de.json > /dev/null\n'
python -m json.tool translations/de.json > /dev/null
run git diff --check

section "Restart Service"
run sudo systemctl restart "$SERVICE_NAME"
run sudo systemctl status "$SERVICE_NAME" --no-pager

section "Recent Logs"
run sudo journalctl -u "$SERVICE_NAME" -n 50 --no-pager

section "Test URLs"
cat <<'URLS'
https://eliashauksson.com
https://eliashauksson.com/projects
https://eliashauksson.com/logbook
https://eliashauksson.com/admin
https://eliashauksson.com/admin/media
URLS

section "Done"
echo "Live update finished."
