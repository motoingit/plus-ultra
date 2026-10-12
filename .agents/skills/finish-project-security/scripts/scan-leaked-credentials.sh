
#!/usr/bin/env bash
# Final repository secret scan.
# Exit codes:
#   0  = both scans clean
#   1  = secrets detected
#   2  = incomplete/error
#   124 = timeout

set -uo pipefail

readonly SCAN_TIMEOUT=25
readonly GITLEAKS_TIMEOUT=20
readonly FINDINGS_EXIT=23

if ! command -v gitleaks >/dev/null 2>&1; then
    echo "INCOMPLETE: Gitleaks is not installed."
    exit 2
fi

if ! command -v git >/dev/null 2>&1; then
    echo "INCOMPLETE: Git is not installed."
    exit 2
fi

if ! ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; then
    echo "INCOMPLETE: This directory is not inside a Git repository."
    exit 2
fi

cd "$ROOT" || {
    echo "INCOMPLETE: Cannot enter repository root."
    exit 2
}

TMP_DIR="$(mktemp -d)" || {
    echo "INCOMPLETE: Cannot create temporary scan files."
    exit 2
}
trap 'rm -rf "$TMP_DIR"' EXIT

run_scan() {
    local label="$1"
    shift
    local output="$TMP_DIR/scan.log"
    local status

    : >"$output"

    echo
    echo "=== $label ==="

    timeout --signal=TERM --kill-after=2s "${SCAN_TIMEOUT}s" \
        gitleaks "$@" \
        --redact \
        --exit-code "$FINDINGS_EXIT" \
        --timeout "$GITLEAKS_TIMEOUT" \
        >"$output" 2>&1
    status=$?

    # Gitleaks redacts secrets; do not generate or print raw JSON reports.
    cat "$output"

    case "$status" in
        0)
            echo "CLEAN: $label"
            return 0
            ;;
        "$FINDINGS_EXIT")
            echo "FINDINGS: $label detected potential secrets."
            return 1
            ;;
        124|137)
            echo "INCOMPLETE: $label exceeded its timeout."
            return 2
            ;;
        *)
            echo "INCOMPLETE: $label failed (exit code $status)."
            return 2
            ;;
    esac
}

echo "Final security scan"
echo "Repository: $ROOT"
echo "Scope: current files and Git history"
echo "Per-scan hard limit: ${SCAN_TIMEOUT}s"
echo "Maximum normal scan time: about 50s"

overall=0

run_scan "Current files" dir "$ROOT"
status=$?
if (( status == 1 )); then
    overall=1
elif (( status == 2 )); then
    overall=2
fi

# Do not begin another scan if the first one already timed out/failed.
if (( overall != 2 )); then
    run_scan "Git history" git "$ROOT"
    status=$?

    if (( status == 2 )); then
        overall=2
    elif (( status == 1 && overall == 0 )); then
        overall=1
    fi
else
    echo "Git history scan skipped because the current-files scan was incomplete."
fi

echo
case "$overall" in
    0)
        echo "RESULT: CLEAN — both scans completed without detected secrets."
        exit 0
        ;;
    1)
        echo "RESULT: SECRETS DETECTED — review findings before publishing."
        exit 1
        ;;
    *)
        echo "RESULT: INCOMPLETE — do not treat this as a clean scan."
        exit 2
        ;;
esac

