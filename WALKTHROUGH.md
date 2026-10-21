# WALKTHROUGH.md — Follow one example

This document follows one supplied profile from input to validation report. It is the written alternative to the requested walkthrough recording. You can follow it with Python or Docker Compose; both routes use the same code, files and rules.

## 1. Look at the input

Open `inputs/primary.json`.

It contains a `policy` object and a `profiles` list. The policy defines allowed hostname suffixes and secret prefixes. Each item in `profiles` is one scan configuration.

The third profile contains:

```json
{
  "name": "API-Nightly",
  "target": "https://api.north-staging.example.test/",
  "schedule": "daily 7:30",
  "auth": {
    "type": "none"
  },
  "max_duration_minutes": true
}
```

These are the settings the program will check. They contain deliberate mistakes.

## 2. Run the command

Choose one route from the project directory.

**With Python 3.10 or later:**

```powershell
python app.py --input inputs/primary.json
```

**With Docker Desktop running in Linux-container mode:**

```powershell
docker compose run --build --rm validator --input inputs/primary.json
```

Here, `validator` is the application service defined in `compose.yaml`. It is not a filename. The `--input` argument selects the primary JSON file. The first Compose run builds the image, including the existing 18-test suite, before executing the validator.

Both commands reach the same workflow: `app.py` reads JSON, `validator.py` checks the rules, and `diagnostics.py` prepares the report. Docker supplies the Python environment; Compose supplies the saved runtime settings.

Follow the same report below whichever route you choose. No target website is contacted.

## 3. Find this profile in the report

Look for:

```json
"index": 2,
"name": "API-Nightly",
"valid": false
```

Index `2` means the third profile because indexes start at zero.

`valid: false` means the program found at least one error. This profile has **four**:

| Field | Code | Why it fails |
| --- | --- | --- |
| `max_duration_minutes` | `type` | `true` is a boolean; the rule requires an integer. |
| `name` | `duplicate` | Profile 0 already uses `api-nightly`; uniqueness ignores case. |
| `name` | `invalid` | The required name format allows lowercase letters, not uppercase. |
| `schedule` | `invalid` | The hour needs two digits: `07:30`. |

The same name receives two errors because it breaks two independent rules.

## 4. Read an individual diagnostic

One error is:

```json
{
  "path": "$.profiles[2].max_duration_minutes",
  "code": "type",
  "message": "Expected int"
}
```

Read the path from left to right:

```text
$                       Start at the top of the input
.profiles               Select the profiles list
[2]                     Select its third profile
.max_duration_minutes   Identify the field with the problem
```

This tells the person editing the configuration exactly where to make a correction.

The program reports the problems; it does not rewrite the input.

## 5. Understand the other results

Profile 0 passes and has empty error and warning lists.

Profile 1 has an unknown `owner` field. That produces a warning, but the profile remains valid because warnings do not count as errors.

Elsewhere, primary profile 4 demonstrates a URL trap: an allowed-looking domain appears before `@`, but the actual hostname is `relay.example`. The validator checks the parsed hostname and correctly rejects it.

Detected secrets receive a `secret` error without exposing their values. Their paths do not receive additional validation errors. The location text inside an error or warning is protected too: if a secret was accidentally used as an unknown field name, that part of the location is hidden. Quotes and backslashes in a field name do not bypass this protection. Existing secret tests cover these cases; the suite remains at 18 test methods.

## 6. Check the batch summary

At the end:

```json
"summary": {
  "errors": 13,
  "invalid": 5,
  "profiles": 7,
  "valid": 2,
  "warnings": 2
}
```

These totals match the primary expectations in the README. The command returns exit **1** because some profiles are invalid, while still producing the report.

## 7. Verify and repeat with another policy

Run the existing test suite using the route you chose.

**Python:**

```powershell
python -m unittest discover -s tests -p "*_test.py" -v
```

**Compose:**

```powershell
docker compose run --rm --entrypoint python validator -m unittest discover -s tests -p "*_test.py" -v
```

Expect **18 tests passing** and exit **0**. Both routes run the same suite. Section 5 of `SUBMISSION.md` lists all 18 tests and their expected behavior.

For one concrete example, the duration test starts with a valid profile and changes only its maximum duration:

| Value tested | Expected result |
| --- | --- |
| `5` or `240` | Accepted: both limits are included. |
| `4` or `241` | One `invalid` error at `max_duration_minutes`. |
| `true`, `45.0`, `"45"` or `null` | One `type` error at that field. |

The test compares the actual error path and code with these expectations. A mismatch makes the test fail. The `test_duration_boundaries_and_types ... ok` line in the verbose output confirms all these cases passed.

Now select the second team's input using the same route.

**Python:**

```powershell
python app.py --input inputs/secondary.json
```

**Compose:**

```powershell
docker compose run --rm validator --input inputs/secondary.json
```

The validator reads the second file's policy automatically. Profile 0 passes; profile 1 has a disallowed host and excessive duration; profile 2 has an unused auth reference and a floating-point duration; profile 3 contains a secret in an unknown auth field. Totals are **4 profiles, 1 valid, 3 invalid, 5 errors and 1 warning**, with exit **1**.

For saved results, open `evidence/primary-report.json`, `evidence/secondary-report.json` and `evidence/tests.txt`. There is one report per fixture because the full Python, Docker and Compose reports matched. `evidence/verification.json` records the commands and outcomes for each run method. Normal program runs do not add files to the evidence folder.

## 8. Why Docker and Compose are optional

The assignment asks for a reusable validator CLI. That remains the core deliverable and runs directly with Python's standard library.

Docker was added after the core was verified to provide a consistent local Python environment. Compose makes that option easier to use by keeping the container settings in `compose.yaml`. They do not change the validator's business rules or its output.

This is not a public deployment: there is no hosted application, published image or exposed application port. The Compose container has no network, runs as a non-root user, and uses a read-only root filesystem. Its small temporary directory lets the existing tests create temporary input files. The first build may need internet access to download the base image.

The README permits optional improvements to the local developer experience, says public deployment is outside core scope, and states that full marks are available on the core alone. Docker and Compose are conveniences a reviewer can choose, not requirements for running or assessing the solution.

Sections 11 and 12 of `SUBMISSION.md` give the full container instructions, including saving a report and selecting another input file. The README itself remains the company's original assignment text.
