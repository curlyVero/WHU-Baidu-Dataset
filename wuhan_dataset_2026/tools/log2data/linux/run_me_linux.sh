#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-}"

if [[ -z "${TARGET}" ]]; then
  read -r -p "Input data folder path: " TARGET
fi

if [[ -z "${TARGET}" ]]; then
  echo "No folder provided."
  exit 1
fi

if [[ ! -d "${TARGET}" ]]; then
  echo "Folder not found:"
  echo "${TARGET}"
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "Python is not installed or not in PATH."
  exit 1
fi

if "${PYTHON_BIN}" "${SCRIPT_DIR}/convert_android_logs.py" --root-dir "${TARGET}"; then
  :
else
  status=$?
  echo
  echo "Conversion failed with exit code ${status}."
  exit "${status}"
fi

echo
echo "Output written under:"
echo "${TARGET}"
