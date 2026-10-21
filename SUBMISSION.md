# Scan profile validator — submission report

A Python command-line tool that validates scan configurations before submission. It reports every detected problem with a precise JSON path, separates errors from warnings, and hides detected secret values in display text. It reads local files and does not scan websites or contact external systems.

This report follows the README's requested handoff: a run guide, a decision/work log, an AI-use note, and a written walkthrough.

## 1. Run guide and verification

### Requirements and commands

Python 3.10 or later is sufficient. No additional packages or accounts are required. Run from the extracted project directory:

```sh
python --version
python app.py --help
python -m unittest discover -s tests -p "*_test.py" -v
python app.py --input inputs/primary.json
python app.py --input inputs/secondary.json
```

Use `python3` if that is the name of your Python 3 interpreter. Recorded verification used Python 3.13.2 on Windows.

The test command should finish with `Ran 18 tests` and `OK`. Both fixture commands should print JSON and exit **1** because their input deliberately contains invalid settings.

| Command or input | Expected result | Exit code |
| --- | --- | ---: |
| Unit suite | 18 passing test methods | 0 |
| Primary input | 7 profiles; 2 valid; 5 invalid; 13 errors; 2 warnings | 1 |
| Secondary input | 4 profiles; 1 valid; 3 invalid; 5 errors; 1 warning | 1 |

The primary expectations come directly from the README. Secondary expectations were derived by checking every supplied profile against the written rules and its own policy; the README does not supply secondary totals.

### Reading a diagnostic

```json
{
  "path": "$.profiles[2].max_duration_minutes",
  "code": "type",
  "message": "Expected int"
}
```

This identifies the third profile's duration: the supplied value is a boolean, while the rule requires an integer. Indexes start at zero. A profile is valid when its error list is empty; warnings do not invalidate it. Diagnostic lists sort by path, then code, and profiles retain input order.

### Primary input: errors

Each row below represents exactly one error, including when two errors concern the same field. Primary profile 0 (`api-nightly`) has no diagnostics. Profile 1 (`portal-weekly`) has no errors and remains valid with its warning.

| JSON path | Code | Explanation |
| --- | --- | --- |
| `$.profiles[2].max_duration_minutes` | `type` | The supplied boolean is not an integer duration. |
| `$.profiles[2].name` | `duplicate` | The name repeats profile 0 when compared ignoring case. |
| `$.profiles[2].name` | `invalid` | Uppercase letters violate the required lowercase name format. |
| `$.profiles[2].schedule` | `invalid` | 7:30 needs a two-digit hour: 07:30. |
| `$.profiles[3].auth.token_ref` | `secret` | The value starts with a configured secret prefix; its contents are hidden. |
| `$.profiles[4].auth.token_ref` | `not_allowed` | Recorded authentication does not use token_ref. |
| `$.profiles[4].target` | `invalid` | The parsed hostname is relay.example, outside the allowed suffixes. |
| `$.profiles[5].exclude_paths[1]` | `invalid` | static does not start with a slash. |
| `$.profiles[5].exclude_paths[2]` | `duplicate` | This repeats the earlier /admin entry. |
| `$.profiles[5].target` | `invalid` | The URL uses HTTP instead of HTTPS. |
| `$.profiles[6].api_key` | `secret` | The value starts with a configured secret prefix; its contents are hidden. |
| `$.profiles[6].auth.token_ref` | `missing` | Bearer authentication requires token_ref. |
| `$.profiles[6].schedule` | `missing` | The required schedule field is absent. |

### Primary input: warnings

| JSON path | Code | Explanation |
| --- | --- | --- |
| `$.profiles[1].owner` | `unknown_field` | owner is not a recognized profile field. |
| `$.profiles[6].api_key` | `unknown_field` | api_key is not a recognized profile field. |

### Secondary input: errors

Profile 0 (`mobile-api-daily`) passes without diagnostics, including the valid lower duration boundary of 5 minutes and the midnight schedule. Profiles 1, 2 and 3 are invalid for the reasons below. The same validator is used without changes.

| JSON path | Code | Explanation |
| --- | --- | --- |
| `$.profiles[1].max_duration_minutes` | `invalid` | 241 exceeds the maximum duration of 240. |
| `$.profiles[1].target` | `invalid` | The hostname does not end with this file's allowed mobile suffix. |
| `$.profiles[2].auth.recording_id` | `not_allowed` | Authentication type none does not use recording_id. |
| `$.profiles[2].max_duration_minutes` | `type` | 45.0 is a JSON floating-point number, not an integer. |
| `$.profiles[3].auth.token` | `secret` | The value starts with a configured secret prefix; its contents are hidden. |

### Secondary input: warnings

| JSON path | Code | Explanation |
| --- | --- | --- |
| `$.profiles[3].auth.token` | `unknown_field` | token is not a recognized auth field. |

### Fatal input and exit codes

```sh
python app.py --input inputs/malformed-input.txt
```

This returns exit **2**, a readable line/column error on stderr and no stdout. Missing files and invalid input structure also return 2. A valid batch, including an empty batch, returns **0** with a JSON report; an invalid batch returns **1** with its report. In PowerShell, inspect `$LASTEXITCODE` immediately after a CLI command; in a POSIX shell, use `echo $?`.

### Recorded evidence and meaningful checks

- [tests/app_test.py](tests/app_test.py): executable assertions for CLI behavior and validation results.
- [evidence/tests.txt](evidence/tests.txt): actual output of the 18 passing tests.
- [evidence/verification.json](evidence/verification.json): interpreter, commands, exit statuses and summary results.
- [evidence/primary-report.json](evidence/primary-report.json): complete primary output.
- [evidence/secondary-report.json](evidence/secondary-report.json): complete secondary output.
- [evidence/malformed-error.txt](evidence/malformed-error.txt): captured fatal diagnostic.

The suite asserts exact error paths and codes for both fixtures. Constructed boundary cases accept durations 5 and 240 and reject 4 and 241. Other checks cover boolean and floating-point durations, case-insensitive duplicate names, parsed hostname matching, schedule limits, auth rules, excluded-path duplicates, warnings-only validity, nested secrets, redaction, exit codes 0/1/2, an empty batch, malformed envelopes, deterministic output and unchanged input.

## 2. Decision and work log

### Priorities and deferred work

The priority was a usable, reusable validator with reproducible verification. The implementation keeps the existing `--input` interface, reads policy from the payload, and exposes validation through `validate_profiles` in [app.py](app.py). Tests exercise both the function and CLI. The implementation remains standard-library-only.

No web service, database, deployment, Docker setup or large architecture was added. These are unnecessary for the required local workflow, and the README awards full marks for the core alone. Verification and a clear handoff took priority over optional features.

### Obstacle and response: integer validation

Python treats booleans as instances of int. A normal `isinstance(value, int)` check could therefore accept the primary profile 2 duration incorrectly. Exact type checking rejects it with `type` at `$.profiles[2].max_duration_minutes`. The boundary tests also confirm that real integers at 5 and 240 are accepted.

### Validation and refinement: secret redaction

Review found that an early whole-report replacement could change a required diagnostic code if a custom secret value matched the word `type`. A separate case showed that later replacements could alter an inserted `[REDACTED]` marker.

Two regression tests were added and failed on the old implementation. The fix preserves diagnostic codes and performs a single substitution pass on display text. Both tests pass with the final implementation:

- `test_redaction_preserves_diagnostic_codes`
- `test_redaction_does_not_rewrite_its_own_marker`

### Other decisions supported by fixture evidence

- **Parse the hostname:** primary profile 4 is rejected because its real host is `relay.example`; the allowed-looking domain before `@` is user information.
- **Find secrets before other checks:** primary `$.profiles[3].auth.token_ref` receives only `secret`, without an additional format error at that path.
- **Apply each file's policy:** secondary profile 1 is rejected under the narrower mobile suffix, without modifying the code.

### Assumptions, known limits and next step

- Empty policy arrays are accepted because the specification gives no minimum length. Hostnames are lowercased and configured suffixes are matched literally. A leading-dot suffix requires a subdomain.
- Unknown root/policy keys are ignored. Unknown profile/auth keys generate warnings. Their nested values are still checked for secrets. Invalid auth types skip dependent reference checks.
- Secret names and secret text in paths are redacted; non-string names become null. Unusual keys use quoted bracket paths. Redacting a path prioritizes confidentiality over preserving its exact spelling.
- Fixed JSON keys, required diagnostic codes and the redaction marker remain protocol text. A custom policy that labels these exact words as secrets conflicts with the required output vocabulary; the implementation preserves the protocol and redacts input-derived display text. The supplied policies do not create this conflict.
- Detection follows the requested prefix rule, rather than a general credential detector. No remote validation occurs. Very large or deeply nested inputs have no explicit resource limits. Adding size/depth limits and tests would be the next step if broader input sizes were required.

## 3. AI-use note

- I used Codex to help me understand the requirements and as a coding, testing and documentation assistant. It assisted with the implementation; I do not claim the code was written without AI.
- I directed the work through requests for implementation, a second review, corrections, verification instructions and clearer submission material. I asked for explanations when I did not understand a result.
- I ran the unit suite and both supplied fixture commands locally, then shared the terminal output for review. The run showed 18 passing test methods and the expected primary and secondary reports.
- One concrete corrected AI output was the broad redaction step. Review found it could overwrite the diagnostic code `type` and could rewrite its own replacement marker. Two regression tests reproduced the defects before correction and passed afterward; these checks are included in the final suite.
- The solution uses only Python's standard library. No Docker, persistence layer or multi-module architecture was implemented or claimed. I remain responsible for understanding and reviewing the final submission and checking that the delivered behavior follows the README.

## 4. Accessible walkthrough

[WALKTHROUGH.md](WALKTHROUGH.md) is the written alternative to the requested 3–5 minute recording. It explains the core workflow, representative diagnostics, a URL edge case, redaction refinement and reproducible execution evidence. The walkthrough and recorded evidence accompany the runnable source, tests and supplied inputs in the submission archive.
