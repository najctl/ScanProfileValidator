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

**Automated checks:** 18 passing test methods; exit 0.

| Input | Profiles | Valid | Invalid | Errors | Warnings | Exit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Primary | 7 | 2 | 5 | 13 | 2 | 1 |
| Secondary | 4 | 1 | 3 | 5 | 1 | 1 |

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

### Primary input: profile results

Field paths are relative to `$.profiles[index]`. Each diagnostic appears on its own line within the profile row. A profile with no errors is valid, even when it has warnings.

| Index / name | Errors | Warnings |
| --- | --- | --- |
| 0 · api-nightly | None | None |
| 1 · portal-weekly | None | `owner` → unknown_field |
| 2 · API-Nightly | `max_duration_minutes` → type<br>`name` → duplicate<br>`name` → invalid<br>`schedule` → invalid | None |
| 3 · billing-scan | `auth.token_ref` → secret | None |
| 4 · partner-export | `auth.token_ref` → not_allowed<br>`target` → invalid | None |
| 5 · search-crawl | `exclude_paths[1]` → invalid<br>`exclude_paths[2]` → duplicate<br>`target` → invalid | None |
| 6 · docs-preview | `api_key` → secret<br>`auth.token_ref` → missing<br>`schedule` → missing | `api_key` → unknown_field |

### Secondary input: profile results

Field paths are relative to `$.profiles[index]`. Each diagnostic appears on its own line within the profile row. A profile with no errors is valid, even when it has warnings.

The same code applies this file's narrower mobile policy without changes.

| Index / name | Errors | Warnings |
| --- | --- | --- |
| 0 · mobile-api-daily | None | None |
| 1 · mobile-web-weekly | `max_duration_minutes` → invalid<br>`target` → invalid | None |
| 2 · mobile-push | `auth.recording_id` → not_allowed<br>`max_duration_minutes` → type | None |
| 3 · mobile-legacy | `auth.token` → secret | `auth.token` → unknown_field |

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

The priority was a usable, reusable validator with reproducible verification. The implementation keeps the existing `--input` interface, reads policy from the payload, and exposes validation through `validate_profiles` in [validator.py](validator.py). Tests exercise both the function and CLI. The implementation remains standard-library-only.

No web service, database, deployment, Docker setup or large architecture was added. These are unnecessary for the required local workflow, and the README awards full marks for the core alone. Verification and a clear handoff took priority over optional features.

### Module boundaries

The code is separated by responsibility so validation can be reused without CLI or file handling:

| Module | Responsibility |
| --- | --- |
| [app.py](app.py) | Parse arguments, read UTF-8 JSON, handle fatal errors, print the report and choose the exit code. |
| [validator.py](validator.py) | Validate the input structure, apply policy and field rules, and collect all profile diagnostics. |
| [diagnostics.py](diagnostics.py) | Build JSON paths, redact report text, sort diagnostics and calculate summary counts. |

The processing flow is `app.py → validator.py → diagnostics.py`. Diagnostic formatting does not read files or import the CLI. Validation has no command-line or filesystem dependency. Tests exercise the reusable function and the existing command interface. This split keeps ownership clear without adding a framework or dependencies.

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

- I directed the implementation and review against the README's contract. I chose a three-module split for clear ownership of command-line handling, validation rules and diagnostic formatting, while keeping the solution simple and standard-library-only.
- I used Codex as a coding and documentation assistant to implement and revise the solution. I requested focused changes, a second requirements review, fixes and improvements to the submission structure.
- One concrete validation check was `max_duration_minutes=True`: Python treats booleans as integers, but this contract requires a type error. I verified the final behavior by running the fixture commands and unit suite locally and reviewing the results.
- One corrected AI output was the broad redaction pass. Review exposed changes to the required code `type` and to inserted redaction markers. I requested the fix; two regression tests reproduced the problems before correction and passed afterward.
- I refined my instructions when the report layout did not match the intended handoff. I requested results grouped by profile, with each diagnostic on its own line, and a separation of code responsibilities into three Python files.
- Codex accelerated implementation and documentation. I remain responsible for the final review, accepted changes, testing and submission. The verification record includes 18 passing test methods and both fixture reports.

## 4. Accessible walkthrough

[WALKTHROUGH.md](WALKTHROUGH.md) is the written alternative to the requested 3–5 minute recording. It explains the core workflow, representative diagnostics, a URL edge case, redaction refinement and reproducible execution evidence. The walkthrough and recorded evidence accompany the runnable source, tests and supplied inputs in the submission archive.
