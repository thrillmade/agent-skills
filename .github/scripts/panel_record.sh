#!/usr/bin/env bash
# Checks the census panel's record against a closed vocabulary and rewrites it
# from fixed strings only.
#
#   panel_record.sh <census-dir> [<panel-exit-code>]
#
# WHY THIS EXISTS. census_panel.py runs next to a third-party SDK that holds an
# API key, in a public repository whose Actions log anyone can read. The
# workflow step that runs it sends both of its streams to /dev/null and removes
# the runner's file-command variables from its environment, and this script is
# the only reader of the raw record, panel_status.json. It checks every field
# against the vocabulary below, rewrites the record from the checked fields and
# fixed phrases, and prints that rewritten record on stdout. Every step that
# prints or uploads from the record runs this script immediately before and
# reads its fields once from this output, never from the file again. It also
# removes any of the census files that is not a regular file (a directory, a
# symlink, a FIFO), and treats such a record as bad_record. It is idempotent.
#
# THE GUARANTEE, AND ITS LIMIT. Against an honest or buggy dependency,
# whatever the SDK raises, logs, warns or prints never reaches the public
# Actions log, the job summary, an issue or an uploaded file, and a failure is
# reported from a validated record. It does not claim to contain a deliberately
# malicious dependency: code that holds the API key and can open a network
# connection cannot be contained by anything in this workflow. That threat is
# answered by pinning the dependency by hash, a separate change, and is out of
# scope here. Nor is the record the only panel information a reader sees:
# verdicts.json and the digest carry the model's answer by design, and are
# filed and uploaded as written.
#
# THE VOCABULARY (a test pins each list against the script that writes them):
#   state        ran | off | held_back | failed
#   reason_code  one of CODES below; `reason` is never read, the phrase comes
#                from `phrase`
#   stage        startup | sdk_import | client | call | parse | write
#   http_status  an integer 100..599, or absent
#   exc_class    a name on EXC_CLASSES; any other name becomes "unrecognised"
#   verdicts, keeps  integers 0..99999
# A value must equal one listed word exactly (a run of words, a stray space or
# newline, or an empty string is outside the list). exit_status is the script's
# exit status, an integer 0..255, present when the script exited non-zero.
# A field of the wrong type, or outside its list, replaces the whole record with
# state failed / reason_code bad_record. A non-zero exit code of the script
# overrides a state that would have been green.
#
# EXC_CLASSES: every built-in exception name (a test compares this list with
# the running interpreter's `builtins`), the exception classes of the
# `anthropic` SDK (src/anthropic/_exceptions.py on the SDK's main branch,
# github.com/anthropics/anthropic-sdk-python), and this repository's own three.
set -uo pipefail

DIR="${1:?census directory}"
RC="${2:-0}"
NONREG=0
FILE="${DIR}/panel_status.json"

CODES=" no_key partial_census authentication permission model_unavailable client_error rate_limited service_error timeout connection invalid_answer sdk_missing key_blank unexpected script_exit bad_record "
STAGES=" startup sdk_import client call parse write "
EXC_CLASSES=" \
BaseException BaseExceptionGroup Exception ExceptionGroup GeneratorExit KeyboardInterrupt SystemExit \
ArithmeticError AssertionError AttributeError BlockingIOError BrokenPipeError BufferError BytesWarning \
ChildProcessError ConnectionAbortedError ConnectionError ConnectionRefusedError ConnectionResetError \
DeprecationWarning EOFError EncodingWarning EnvironmentError FileExistsError FileNotFoundError \
FloatingPointError FutureWarning IOError ImportError ImportWarning IndentationError IndexError \
InterruptedError IsADirectoryError KeyError LookupError MemoryError ModuleNotFoundError NameError \
NotADirectoryError NotImplementedError OSError OverflowError PendingDeprecationWarning PermissionError \
ProcessLookupError PythonFinalizationError RecursionError ReferenceError ResourceWarning RuntimeError \
RuntimeWarning StopAsyncIteration StopIteration SyntaxError SyntaxWarning SystemError TabError TimeoutError \
TypeError UnboundLocalError UnicodeDecodeError UnicodeEncodeError UnicodeError UnicodeTranslateError \
UnicodeWarning UserWarning ValueError Warning ZeroDivisionError JSONDecodeError CancelledError \
AnthropicError APIError APIResponseValidationError APIWebhookValidationError APIStatusError \
APIConnectionError APITimeoutError RetryableError CredentialsError IdentityTokenFileError \
BadRequestError AuthenticationError PermissionDeniedError NotFoundError RequestTimeoutError ConflictError \
PreconditionFailedError ContentTooLargeError UnprocessableEntityError RateLimitError \
RequestHeaderFieldsTooLargeError ClientClosedRequestError InternalServerError HTTPNotImplementedError \
ServiceUnavailableError GatewayTimeoutError OverloadedError \
PanelValidationError PanelSdkMissing PanelNoText "

phrase() {
  case "$1" in
    no_key) echo "no API key is configured" ;;
    partial_census) echo "the census is partial" ;;
    authentication) echo "the API key was refused (HTTP 401)" ;;
    permission) echo "the API key lacks permission for this request (HTTP 403)" ;;
    model_unavailable) echo "the model was not found or is not available to this key (HTTP 404)" ;;
    client_error) echo "the API refused the request" ;;
    rate_limited) echo "the API rate limit was hit (HTTP 429)" ;;
    service_error) echo "the API service failed" ;;
    timeout) echo "the API call timed out" ;;
    connection) echo "the API could not be reached" ;;
    invalid_answer) echo "the model's answer could not be used" ;;
    sdk_missing) echo "the anthropic package is not installed" ;;
    key_blank) echo "the API key is set but blank" ;;
    unexpected) echo "an unexpected exception was raised" ;;
    script_exit) echo "the panel script exited with a failure status" ;;
    bad_record) echo "panel_status.json held a value outside the allowed set" ;;
    *) echo "" ;;
  esac
}

# Exact membership: the whole value must equal one listed word. A run of listed
# words, a value with a space, a newline or nothing in it does not match.
in_list() {
  local w
  for w in $2; do [ "$w" = "$1" ] && return 0; done
  return 1
}

# One field, type-checked by jq. Sets $1 to the value and $1_T to a tag: N for
# null or absent, S for a string, ? for any other type. The value is kept
# byte for byte (a trailing newline survives), so an exact comparison sees it.
field() {
  local out
  out="$({ jq -j --arg k "$2" '
    .[$k] as $v
    | if $v == null then "N"
      elif ($v | type) == "string" then "S" + $v
      else "?" end' "$FILE" 2>/dev/null | head -c 200; printf x; })"
  out="${out%x}"
  printf -v "$1_T" '%s' "${out:0:1}"
  printf -v "$1" '%s' "${out:1}"
}

# Anything in the census directory that is not a regular file is removed: a
# directory would be expanded by the upload step, a FIFO would hang a reader, a
# symlink would be followed.
for f in panel_status.json verdicts.json digest.md census.json; do
  if [ -L "${DIR}/${f}" ] || { [ -e "${DIR}/${f}" ] && [ ! -f "${DIR}/${f}" ]; }; then
    rm -rf "${DIR:?}/${f}"
    [ "$f" != panel_status.json ] || NONREG=1
  fi
done

bad() {
  STATE=failed CODE=bad_record STAGE="" HTTP="" CLS="" BG="" N=0 K=0 EXS=""
}

# The script's exit status is the shell's own value; anything else is 255.
[[ "$RC" =~ ^[0-9]{1,3}$ ]] && [ "$RC" -le 255 ] || RC=255

STATE="" CODE="" STAGE="" HTTP="" CLS="" BG="" N=0 K=0 EXS=""
HAVE=0
if [ "$NONREG" = 1 ]; then
  HAVE=1
  bad
elif [ -f "$FILE" ]; then
  HAVE=1
  if ! jq -e 'type == "object"' "$FILE" >/dev/null 2>&1; then
    bad
  else
    field STATE state; field CODE reason_code; field STAGE stage
    field CLS exc_class; field BG background_error_class
    HTTP="$(jq -r '.http_status | if . == null then ""
      elif type == "number" and . == floor then tostring else "?" end' "$FILE" 2>/dev/null | head -c 20)"
    N="$(jq -r '.verdicts | if . == null then "0" elif type == "number" and . == floor then tostring else "?" end' "$FILE" 2>/dev/null | head -c 20)"
    K="$(jq -r '.keeps | if . == null then "0" elif type == "number" and . == floor then tostring else "?" end' "$FILE" 2>/dev/null | head -c 20)"
    EXS="$(jq -r '.exit_status | if . == null then ""
      elif type == "number" and . == floor then tostring else "?" end' "$FILE" 2>/dev/null | head -c 20)"
    ok=1
    [ "$STATE_T" = S ] && in_list "$STATE" " ran off held_back failed " || ok=0
    [ "$CODE_T" = N ] || { [ "$CODE_T" = S ] && in_list "$CODE" "$CODES"; } || ok=0
    [ "$STAGE_T" = N ] || { [ "$STAGE_T" = S ] && in_list "$STAGE" "$STAGES"; } || ok=0
    [ -z "$HTTP" ] || { [[ "$HTTP" =~ ^[0-9]{3}$ ]] && [ "$HTTP" -ge 100 ] && [ "$HTTP" -le 599 ]; } || ok=0
    [ -z "$EXS" ] || { [[ "$EXS" =~ ^[0-9]{1,3}$ ]] && [ "$EXS" -le 255 ]; } || ok=0
    [[ "$N" =~ ^[0-9]{1,5}$ ]] || ok=0
    [[ "$K" =~ ^[0-9]{1,5}$ ]] || ok=0
    # A class is a name, not a sentence: a name off the list is reported as
    # unrecognised and never echoed.
    for c in CLS BG; do
      t="${c}_T"; v="${!c}"
      if [ "${!t}" = N ]; then printf -v "$c" '%s' ""
      elif [ "${!t}" != S ]; then ok=0
      elif ! in_list "$v" "$EXC_CLASSES"; then printf -v "$c" '%s' unrecognised; fi
    done
    [ "$ok" = 1 ] || bad
  fi
fi

# A script that exited non-zero is a failure whatever its record says, unless
# the record already says failed for a reason that needs a person. When the
# caller passes the status, the record carries it as exit_status.
if [ "$#" -ge 2 ]; then
  EXS=""
  [ "$RC" = 0 ] || EXS="$RC"
fi
if [ "$RC" != 0 ]; then
  if [ "$HAVE" = 0 ] || [ "$STATE" != failed ]; then
    HAVE=1; STATE=failed; CODE=script_exit
  else
    case "$CODE" in rate_limited|service_error|timeout|connection|invalid_answer|"") CODE=script_exit ;; esac
  fi
fi

[ "$HAVE" = 1 ] || exit 0

TMP="$(mktemp "${DIR}/.panel_status.XXXXXX")" || exit 1
OUT="$(jq -n --arg state "$STATE" --arg code "$CODE" --arg reason "$(phrase "$CODE")" \
  --arg stage "$STAGE" --arg http "$HTTP" --arg cls "$CLS" --arg bg "$BG" --arg exs "$EXS" \
  --argjson n "${N:-0}" --argjson k "${K:-0}" '{
    state: $state,
    reason_code: (if $code == "" then null else $code end),
    reason: (if $reason == "" then null else $reason end),
    stage: (if $stage == "" then null else $stage end),
    exc_class: (if $cls == "" then null else $cls end),
    background_error_class: (if $bg == "" then null else $bg end),
    http_status: (if $http == "" then null else ($http | tonumber) end),
    exit_status: (if $exs == "" then null else ($exs | tonumber) end),
    verdicts: $n,
    keeps: $k
  }')" || { rm -f "$TMP"; exit 1; }
printf '%s\n' "$OUT" > "$TMP" && mv "$TMP" "$FILE" || { rm -f "$TMP"; exit 1; }
# The validated record is also this script's output: a caller reads its fields
# from here, once, and never opens the file again.
printf '%s\n' "$OUT"
