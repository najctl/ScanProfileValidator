# Scan profile validator

**A local Python CLI that catches invalid scan settings before submission and reports where to fix them.**

The implementation validates every supplied profile against its file's policy, reports errors separately from warnings, and protects detected credential values in displayed output. It performs no scans or network requests. Python 3.10+ and the standard library are sufficient.

**Verified result:** 18 automated tests pass. The primary fixture matches the assignment's exact totals and per-profile error counts. The same validator handles the secondary fixture without code changes.

## Start here

Run these commands from the extracted project directory:

```sh
python -m unittest discover -s tests -p "*_test.py" -v
python app.py --input inputs/primary.json
python app.py --input inputs/secondary.json
```

Use `python3` instead of `python` if that is your Python 3 interpreter's name. The recorded execution environment was Python 3.13.2 on Windows. No dependency installation is needed.

The tests should finish with **`Ran 18 tests` and `OK`**. Both supplied batches deliberately contain invalid profiles, so both CLI runs produce JSON and **exit 1**. This is the expected validation result, not a crash.

| Reviewer task | Where to look |
| --- | --- |
| Inspect the implementation | [app.py](app.py), especially `validate_profiles` |
| Check assertions and boundary cases | [tests/app_test.py](tests/app_test.py) |
| Compare recorded results | [Verification record](evidence/verification.json), [test output](evidence/tests.txt) |
| Inspect complete reports | [Primary report](evidence/primary-report.json), [secondary report](evidence/secondary-report.json) |
| Read the walkthrough instead of watching a video | [WALKTHROUGH.md](WALKTHROUGH.md) |
| Consult the assessment requirements | [README.md](README.md#core-task-and-observable-acceptance-criteria) |

## Using the result

```sh
python app.py --help
python app.py --input inputs/primary.json
```

`--input` selects a UTF-8 JSON file; it defaults to `inputs/primary.json`. The report keeps input profile order. Each profile includes its index, name, validity, and diagnostic lists; the final summary provides batch totals. Errors and warnings sort by path, then code.

A representative primary diagnostic is:

```json
{
  "path": "$.profiles[2].max_duration_minutes",
  "code": "type",
  "message": "Expected int"
}
```

This points to the third profile's duration. Its supplied value is a boolean; the contract requires an integer. A caller can locate the exact field without searching through the batch. Warnings such as `$.profiles[1].owner` flag unknown fields without making the profile invalid.

| Exit | Meaning | Output |
| ---: | --- | --- |
| 0 | Every profile is valid, including an empty batch | JSON report on stdout |
| 1 | At least one profile has errors | JSON report on stdout |
| 2 | File, JSON syntax, or input-structure failure | Readable error on stderr; no stdout |

To verify the fatal-error behavior:

```sh
python app.py --input inputs/malformed-input.txt
```

It should exit 2 with a line/column diagnostic, without printing input contents or a traceback. In PowerShell, run `$LASTEXITCODE` immediately after a CLI command to inspect its exit status; in a POSIX shell, use `echo $?`.

## Verification evidence

The files under [evidence/](evidence/) record actual local executions, not illustrative output. The automated tests independently assert expected field paths and codes as well as totals.

| Input | Profiles | Valid | Invalid | Errors | Warnings | Exit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Primary | 7 | 2 | 5 | 13 | 2 | 1 |
| Secondary | 4 | 1 | 3 | 5 | 1 | 1 |

**Expected-result sources:** the assignment explicitly supplies the primary totals and per-profile counts. Secondary expectations were derived by inspecting each input profile against its policy and the written rules; the assignment asks for this reconciliation without providing totals.

The paths below are relative to `$.profiles[index]`.

### Primary: exact reconciliation

| Index / name | Error paths and codes | Warning paths |
| --- | --- | --- |
| 0 · api-nightly | None | None |
| 1 · portal-weekly | None | `owner`: unknown_field |
| 2 · API-Nightly | `name`: duplicate,| invalid; `schedule`: invalid; `max_duration_minutes`: type | None |
| 3 · billing-scan | `auth.token_ref`: secret | None |
| 4 · partner-export | `target`: invalid; `auth.token_ref`: not_allowed | None |
| 5 · search-crawl | `target`: invalid; `exclude_paths[1]`: invalid; `exclude_paths[2]`: duplicate | None |
| 6 · docs-preview | `schedule`: missing; `auth.token_ref`: missing; `api_key`: secret | `api_key`: unknown_field |

### Secondary: policy reuse

| Index / name | Rule violation | Result |
| --- | --- | --- |
| 0 · mobile-api-daily | None; duration 5 and midnight are valid boundaries | Valid |
| 1 · mobile-web-weekly | Host does not match this file's mobile suffix; duration 241 exceeds 240 | 2 errors |
| 2 · mobile-push | `recording_id` is unused by auth type none; duration 45.0 is a float | 2 errors |
| 3 · mobile-legacy | Unknown `auth.token` contains a detected secret | 1 error, 1 warning |

### What the tests establish

| Area | Checks |
| --- | --- |
| CLI behavior | Help, missing file, truncated JSON, malformed envelopes, exit codes 0/1/2, empty batch |
| Core rules | Case-insensitive name duplicates, schedule boundaries, authentication references, excluded-path duplicates, unknown-field warnings |
| Numeric boundaries | 5 and 240 accepted; 4 and 241 rejected; boolean, float, string and null rejected as integer durations |
| URL interpretation | Uppercase hosts and valid ports accepted; misleading user information, suffix extensions, HTTP and malformed ports rejected |
| Confidentiality | Nested secret detection, secret names hidden, CLI output checked, diagnostic codes preserved, replacement markers stable |
| Repeatability | Deterministic reports and unchanged input; exact error-path/code assertions for both fixtures |

## Decisions and work log

| Decision or obstacle | Response and evidence |
| --- | --- |
| Prioritize a usable core | Completed the local CLI, reusable validation function, tests and handoff before optional features. No server, database, deployment or external packages were added. |
| Python booleans behave like integers | Used exact type checks. Primary `$.profiles[2].max_duration_minutes` receives `type`, while duration 5 remains valid in secondary profile 0. |
| Allowed-looking text can hide a different hostname | Used `urlsplit(...).hostname`. Primary profile 4 is rejected because the actual hostname is `relay.example`, regardless of the domain before `@`. |
| Secret suppression must precede ordinary validation | Scan nested values first. Primary `$.profiles[3].auth.token_ref` receives only `secret`, rather than an additional reference-format error. |
| Review exposed over-redaction | Added two regression tests that failed before the fix: a custom secret value could overwrite the code `type`, and a later replacement could alter an inserted redaction marker. The fix preserves codes and substitutes display text in one pass. Both tests now pass. |
| Demonstrate reuse rather than fixture-specific answers | Read policy from each payload and reconcile secondary results without changing the validator. |

### Assumptions and known limits

- Policy arrays may be empty because no minimum length is specified. Hostnames are lowercased; configured suffixes are matched literally. A leading-dot suffix requires a subdomain, rather than the bare suffix root.
- Unknown root/policy keys are ignored. Unknown profile/auth keys generate warnings, and their nested values are still inspected for secrets. Invalid auth types skip dependent reference checks.
- A secret name is displayed as `[REDACTED]`; a non-string name is displayed as null. Unusual keys use quoted bracket paths. A path containing a detected secret is redacted, prioritizing confidentiality over its exact spelling.
- Fixed JSON keys, required error codes and the replacement marker remain protocol text. A custom policy that classifies one of those exact words as a secret creates a specification conflict; the implementation preserves the required protocol while redacting input-derived display text. This qualification does not affect the supplied fixtures.
- Detection follows the configured string-prefix rule, not a general credential-detection heuristic. There is no DNS lookup or credential verification. Very large or deeply nested inputs have no explicit resource limits; those limits and related tests would be the next improvement if broader input sizes were required.

## AI-use disclosure

Codex was used to explain the assignment and assist with implementation, tests, review and documentation. Its output was checked against the written rules, both supplied fixtures and executed automated tests. The candidate also reran the test suite and both fixture commands and inspected the results during the assisted session.

A concrete corrected AI output was the original whole-report redaction pass. Review showed it could replace a required diagnostic code when a custom secret value was the word `type`. Two regression tests reproduced redaction defects before the change, then passed after narrowing replacement to display text and using a single substitution pass. The final suite contains 18 passing test methods. No private prompt history, account access or real credentials are included.
