# SUBMISSION.md — Start here

## What this project does

This program checks a JSON file containing website-scan settings.

Each set of settings is called a **profile**. A profile describes the website address, scan schedule, authentication method, and maximum duration.

The program checks whether those settings follow the assignment's rules. It returns a report showing:

- Which profiles passed.
- Every error and its location.
- Warnings about unrecognized fields.
- Totals for the entire file.

**It does not visit websites or run scans.**

## 1. Open the project

Extract the submission ZIP, then open a terminal inside the extracted project folder—the folder containing `app.py`.

The project contains:

```text
app.py             Starts the command-line program
validator.py       Checks the validation rules
diagnostics.py     Formats paths, redacts secrets, and builds totals

inputs/            Example files supplied with the assignment
tests/             Automated checks for the program
evidence/          Saved results from executed commands

README.md          The company's assignment
SUBMISSION.md      This guide and the implementation notes
WALKTHROUGH.md     A worked example showing the program in use
```

Keep the three Python files together.

## 2. Check Python

Python **3.10 or later** is required. No additional packages are needed.

Run:

```powershell
python --version
```

If your system uses `python3`, substitute `python3` for `python` in the commands below.

## 3. Run the validator

Start with the first supplied example:

```powershell
python app.py --input inputs/primary.json
```

Here:

- `app.py` starts the program.
- `--input` selects the file to check.
- `inputs/primary.json` contains seven profiles and their policy.

The program prints a JSON report. Its final section should be:

```json
"summary": {
  "errors": 13,
  "invalid": 5,
  "profiles": 7,
  "valid": 2,
  "warnings": 2
}
```

This means **seven profiles were checked: two passed and five failed, with thirteen errors and two warnings altogether.**

These failures are intentional mistakes in the supplied example. The README explicitly requires these primary results.

For a detailed explanation of one profile, read **WALKTHROUGH.md**.

## 4. Check the second example

Run:

```powershell
python app.py --input inputs/secondary.json
```

This file carries a different policy. The program reads that policy automatically; no code change is needed.

Expected totals:

| Input | Profiles | Valid | Invalid | Errors | Warnings |
| --- | ---: | ---: | ---: | ---: | ---: |
| Primary | 7 | 2 | 5 | 13 | 2 |
| Secondary | 4 | 1 | 3 | 5 | 1 |

The README supplies the primary expectations. The secondary expectations were determined by comparing each profile with the written rules and its own policy.

## 5. Run the automated checks

Run:

```powershell
python -m unittest discover -s tests -p "*_test.py" -v
```

The result should end with:

```text
Ran 18 tests in ...s

OK
```

**These tests check the Python program itself.** They are separate from the profiles being validated.

They check rules and behavior such as duplicate names, duration boundaries, URL hostname matching, authentication, secret redaction, malformed input, and exit codes.

The elapsed time can vary between runs. `OK` means the checks passed.

## 6. Understand the exit codes

An exit code lets another script tell whether validation succeeded.

| Code | Meaning |
| ---: | --- |
| `0` | All profiles passed, including an empty batch. |
| `1` | Some profiles failed; the JSON report explains why. |
| `2` | The file could not be processed; a readable error is printed. |

Both supplied JSON examples return **1**, because they deliberately contain invalid profiles.

To check broken JSON:

```powershell
python app.py --input inputs/malformed-input.txt
```

It should print a readable error, produce no JSON report, and return **2**.

In PowerShell, run this immediately afterward to see the exit code:

```powershell
$LASTEXITCODE
```

## 7. Compare the profile results

Each field below belongs to the profile identified in the first column. For example, `schedule` in profile 2 means `$.profiles[2].schedule`.

### Primary input

| Index / name | Errors | Warnings |
| --- | --- | --- |
| 0 · api-nightly | None | None |
| 1 · portal-weekly | None | `owner` → unknown_field |
| 2 · API-Nightly | `max_duration_minutes` → type<br>`name` → duplicate<br>`name` → invalid<br>`schedule` → invalid | None |
| 3 · billing-scan | `auth.token_ref` → secret | None |
| 4 · partner-export | `auth.token_ref` → not_allowed<br>`target` → invalid | None |
| 5 · search-crawl | `exclude_paths[1]` → invalid<br>`exclude_paths[2]` → duplicate<br>`target` → invalid | None |
| 6 · docs-preview | `api_key` → secret<br>`auth.token_ref` → missing<br>`schedule` → missing | `api_key` → unknown_field |

### Secondary input

| Index / name | Errors | Warnings |
| --- | --- | --- |
| 0 · mobile-api-daily | None | None |
| 1 · mobile-web-weekly | `max_duration_minutes` → invalid<br>`target` → invalid | None |
| 2 · mobile-push | `auth.recording_id` → not_allowed<br>`max_duration_minutes` → type | None |
| 3 · mobile-legacy | `auth.token` → secret | `auth.token` → unknown_field |

## 8. Find the execution evidence

The `evidence` folder contains saved output from actual executions.

| File | Contents |
| --- | --- |
| `tests.txt` | Output showing the 18 tests passed. |
| `primary-report.json` | Complete report for the primary input. |
| `secondary-report.json` | Complete report for the secondary input. |
| `malformed-error.txt` | Error produced by the broken JSON example. |
| `verification.json` | Commands, exit codes, environment, timing, and file hashes. |

The validator calculates its results from the selected input. **It does not use the evidence files to obtain its answers.**

## 9. Implementation decisions and work log

**Priority:** complete the required validator, verify both supplied examples, and make execution reproducible. Optional infrastructure was deferred because the assignment's core does not require it.

**Code organization:** `app.py` handles arguments, files, output, and exit codes. `validator.py` applies the rules. `diagnostics.py` handles paths, redaction, sorting, and totals. This keeps validation reusable without command-line dependencies.

**Obstacle:** Python treats booleans as integers in some type checks. Exact type checking prevents `true` from being accepted as a duration. Primary profile 2 and the duration tests verify this behavior.

**Refinement:** an early redaction implementation could overwrite diagnostic codes or rewrite its replacement marker. Two regression checks reproduced those problems. Redaction was corrected, and both checks now pass within the 18-test suite.

**Further review:** nested secret detection now uses an explicit stack to avoid recursion failures. The module imports and execution from another directory were also checked.

### Assumptions and limitations

- Empty policy arrays are accepted because no minimum length is specified.
- Hostnames are lowercased; suffixes are matched literally. URL syntax checking also rejects malformed ports and whitespace.
- Unknown profile and auth fields receive warnings. Unknown root and policy fields are ignored.
- Secret names and secret text in paths are redacted. Fixed report keys and diagnostic codes remain unchanged; policies that classify those protocol words as secrets create a conflict, documented here explicitly.
- Detection follows the configured prefix rule. It is not a general credential detector.
- JSON parsing remains subject to interpreter resource limits. There is no explicit file-size limit; adding a documented limit would be the next step for larger-input use cases.

## 10. AI-use note

- I used Codex as a coding and documentation assistant. I directed the implementation against the assignment and requested reviews and corrections.
- I chose to separate command-line handling, validation, and report formatting into three Python files, while keeping the solution standard-library-only.
- One implementation required correction: broad secret replacement could change the diagnostic code `type` and rewrite the redaction marker. I requested the fix. Both regression checks failed before correction and passed afterward.
- I ran the unit suite and both supplied examples locally and reviewed their output. I remain responsible for the final code, accepted changes, and submission.
