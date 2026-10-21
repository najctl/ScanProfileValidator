# WALKTHROUGH.md — Follow one example

This document demonstrates the program using one profile from the supplied input. It is the written alternative to the requested walkthrough recording.

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

From the project directory:

```powershell
python app.py --input inputs/primary.json
```

`app.py` reads the file and converts the JSON into Python data. It passes that data to `validator.py`, which applies the rules. `diagnostics.py` prepares the final report.

No website is contacted.

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

Detected secrets receive a `secret` error without exposing their values. Their paths do not receive additional validation errors.

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

Run:

```powershell
python -m unittest discover -s tests -p "*_test.py" -v
```

The result should show **18 tests passing**. These checks verify the program's behavior, including duration boundaries, duplicates, authentication, secrets, and error handling.

Then run:

```powershell
python app.py --input inputs/secondary.json
```

The same code reads the second file's policy and produces **5 errors and 1 warning across 4 profiles**. This demonstrates reuse.

For the full saved outputs, open `evidence/primary-report.json`, `evidence/secondary-report.json`, and `evidence/tests.txt`.
