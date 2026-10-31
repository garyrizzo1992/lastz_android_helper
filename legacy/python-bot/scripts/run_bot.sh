#!/usr/bin/env bash
set -euo pipefail

# Parse the complete function before Git updates this script on disk.
lastz_main() {

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" || return $?
repo_dir="$(cd "$script_dir/.." && pwd)" || return $?
env_file="${LASTZ_ENV_FILE:-$repo_dir/.env}"

if [[ -f "$env_file" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$env_file" || return $?
    set +a
fi

python_bin="${LASTZ_PYTHON:-$repo_dir/.venv/bin/python}"
git_remote="${LASTZ_GIT_REMOTE:-origin}"
git_branch="${LASTZ_GIT_BRANCH:-main}"
git_sync="${LASTZ_GIT_SYNC:-true}"

if [[ "${1:-}" == "--preflight" ]]; then
    # A diagnostic must not reset code or change the installed environment.
    cd "$repo_dir" || return $?
    exec "$python_bin" -u main_scrcpy.py "$@"
fi

if [[ -d "${LASTZ_DATA_DIR:-$repo_dir}/deploy.lock" ]]; then
    printf 'LastZ deployment in progress; retrying on the next service start.\n' >&2
    return 1
fi

if [[ "$git_sync" == "true" ]]; then
    if [[ ! -d "$repo_dir/.git" ]]; then
        printf 'LastZ checkout is not a Git repository: %s\n' "$repo_dir" >&2
        return 1
    fi

    printf 'Syncing LastZ from %s/%s...\n' "$git_remote" "$git_branch"
    export GIT_TERMINAL_PROMPT=0
    export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -o BatchMode=yes -o ConnectTimeout=15}"
    git -C "$repo_dir" fetch "$git_remote" "$git_branch" || return $?
    git -C "$repo_dir" reset --hard FETCH_HEAD || return $?
fi

if [[ ! -x "$python_bin" ]]; then
    printf 'LastZ Python is not executable: %s\n' "$python_bin" >&2
    return 1
fi

requirements="$repo_dir/requirements-runtime.txt"
stamp="$repo_dir/.venv/lastz-requirements.sha256"
requirements_hash="$(shasum -a 256 "$requirements")" || return $?
python_version="$("$python_bin" --version)" || return $?
fingerprint="$requirements_hash $python_version"
if [[ ! -f "$stamp" ]] || [[ "$( < "$stamp")" != "$fingerprint" ]]; then
    "$python_bin" -m pip install --disable-pip-version-check -r "$requirements" || return $?
    "$python_bin" -m pip check || return $?
    printf '%s\n' "$fingerprint" > "$stamp" || return $?
fi

revision="$(git -C "$repo_dir" rev-parse --short HEAD)" || return $?
printf 'Starting LastZ revision %s\n' "$revision"
cd "$repo_dir" || return $?
"$python_bin" -u main_scrcpy.py "$@"
}

# A disconnected USB device is an expected operational condition, not a
# reason to churn the LaunchAgent. This mode is enabled only by deployment;
# direct invocations keep fail-fast semantics for preflight and automation.
if [[ "${LASTZ_RETRY_ON_FAILURE:-false}" != "true" ]]; then
    lastz_main "$@"
    exit $?
fi

retry_delay=60
while true; do
    if lastz_main "$@"; then
        exit 0
    fi
    printf 'LastZ exited unsuccessfully; retrying in %ss.\n' "$retry_delay" >&2
    sleep "$retry_delay"
    if (( retry_delay < 300 )); then
        retry_delay=$((retry_delay * 2))
        if (( retry_delay > 300 )); then
            retry_delay=300
        fi
    fi
done
