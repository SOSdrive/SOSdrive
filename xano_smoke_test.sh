#!/bin/bash

# Verify published Xano paths without sending credentials.
# Usage: XANO_SERVICES_URL="https://.../api:service_requests" bash xano_smoke_test.sh

set -euo pipefail

: "${XANO_SERVICES_URL:?XANO_SERVICES_URL must be set}"

request_status() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  if [ -n "$body" ]; then
    curl -sS -o /dev/null -w "%{http_code}" -X "$method" "${XANO_SERVICES_URL%/}${path}" \
      -H "Content-Type: application/json" -d "$body"
  else
    curl -sS -o /dev/null -w "%{http_code}" -X "$method" "${XANO_SERVICES_URL%/}${path}"
  fi
}

assert_status() {
  local method="$1"
  local path="$2"
  local expected="$3"
  local body="${4:-}"
  local actual
  actual="$(request_status "$method" "$path" "$body")"
  if [ "$actual" != "$expected" ]; then
    printf '%s %s expected %s, got %s\n' "$method" "$path" "$expected" "$actual" >&2
    exit 1
  fi
}

assert_status GET "/1/messages" 401
assert_status POST "/1/messages" 401 '{"message_text":"probe"}'
assert_status PATCH "/1/status" 401 '{"status":"completed"}'
assert_status PATCH "/1" 404 '{"status":"completed"}'
assert_status PATCH "/1/messages" 404 '{"status":"completed"}'

printf 'Published Xano path checks passed.\n'
