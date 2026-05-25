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

is_allowed_live_path() {
  case "$1" in
    content/*|static/img/*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

add_dirty_path() {
  local path="$1"

  if is_allowed_live_path "$path"; then
    allowed_dirty_paths+=("$path")
  else
    blocked_dirty_paths+=("$path")
  fi
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

allowed_dirty_paths=()
blocked_dirty_paths=()
while IFS= read -r status_line; do
  [[ -z "$status_line" ]] && continue
  dirty_path="${status_line:3}"

  if [[ "$dirty_path" == *" -> "* ]]; then
    add_dirty_path "${dirty_path%% -> *}"
    add_dirty_path "${dirty_path##* -> }"
  else
    add_dirty_path "$dirty_path"
  fi
done < <(git status --porcelain)

if [[ "${#blocked_dirty_paths[@]}" -gt 0 ]]; then
  echo "Error: refusing to deploy with uncommitted code/config/template changes:" >&2
  printf '  %s\n' "${blocked_dirty_paths[@]}" >&2
  echo "Only local changes under content/ and static/img/ are allowed during deploy." >&2
  exit 1
fi

if [[ "${#allowed_dirty_paths[@]}" -gt 0 ]]; then
  echo "Live content/media changes detected:"
  printf '  %s\n' "${allowed_dirty_paths[@]}"
  echo "These changes will be preserved. They will not be discarded, committed, or stashed."
else
  echo "Live content/media changes detected: none"
fi

section "Pull"
printf '+ git pull --ff-only origin %s\n' "$TARGET_BRANCH"
if ! git pull --ff-only origin "$TARGET_BRANCH"; then
  cat >&2 <<'MSG'
Error: git pull failed.

Local live content/media changes were preserved. If the pull conflicts with
admin-created content or media, resolve it manually on the server, then rerun
this script. No merge conflicts were auto-resolved.
MSG
  exit 1
fi
printf 'Latest commit: %s\n' "$(git log -1 --oneline)"
if [[ "${#allowed_dirty_paths[@]}" -gt 0 ]]; then
  echo "Preserved live content/media changes:"
  printf '  %s\n' "${allowed_dirty_paths[@]}"
fi

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
