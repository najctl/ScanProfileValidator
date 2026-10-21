# Written walkthrough

This is the accessible text alternative to the requested 3–5 minute recording. Follow the commands from the project directory to reproduce the demonstration.

## 1. Purpose and entry point

This tool validates scan settings before a separate scanning system would use them. It reads a local JSON file and produces a JSON report. It does not scan websites, schedule jobs, resolve hostnames, or retrieve credentials.

Start with:

```sh
python app.py --input inputs/primary.json
```

The CLI in `app.py` loads the file as UTF-8 JSON, then calls `validate_profiles` in `validator.py`. `diagnostics.py` owns JSON paths, safe output formatting, sorting and summary totals. That function can also be imported by another Python caller. Its first responsibility is to check the input structure: an object containing a policy and an array of profile objects. If that structure is unusable, the CLI exits 2 and prints a readable error to stderr without a report on stdout.

## 2. Validation and the report

Each profile is checked against the README rules and the policy carried by its own file. Names have format and uniqueness requirements; URLs require HTTPS and an allowed parsed hostname; schedules require exact day/time formatting; durations must be integers between 5 and 240. Authentication type determines which reference is required and which references are forbidden. Excluded paths must be strings beginning with a slash, without exact repetitions.

The primary report's first profile is valid and has empty diagnostic lists. Profile 1 is also valid, despite a warning for its unknown `owner` field. This demonstrates the distinction between warnings and errors.

Profile 2 has four errors: its uppercase name is invalid and repeats the earlier name ignoring case; its schedule has a one-digit hour; its duration is a boolean. The precise path `$.profiles[2].max_duration_minutes` identifies the third profile's duration. Python treats booleans as instances of int, so validation uses an exact integer type check to avoid accepting them accidentally.

Problems are collected rather than stopping at the first error. Profiles retain input order; errors and warnings sort by path and code. The final summary counts profiles, validity, errors and warnings. Primary totals are 7 profiles, 2 valid, 5 invalid, 13 errors and 2 warnings, exactly as required by the assignment. Exit 1 communicates invalid settings while still returning the usable JSON report.

## 3. Two important edge cases

Primary profile 4 contains an allowed-looking domain before an at-sign. That portion is URL user information; its actual hostname is `relay.example`. Parsing the hostname, rather than searching the full URL for a domain substring, correctly rejects it.

Secret detection runs recursively, including inside unknown fields. A detected secret receives only a secret error at its path. Unknown fields may still receive warnings. Primary profile 6 demonstrates both at `api_key`, without printing the value. Secret names and paths are redacted too.

A subsequent review found that broad replacement could overwrite diagnostic codes and rewrite inserted redaction markers. Two new regression tests failed on the old implementation and passed after the fix. The code now preserves required codes and replaces display text in a single pass. The report documents the interpretation for custom policies whose secret words collide with fixed protocol text.

## 4. Evidence and reuse

Run the verification suite:

```sh
python -m unittest discover -s tests -p "*_test.py" -v
```

The recorded result is 18 tests passing. Tests check exact diagnostic paths/codes, boundary durations, URL host parsing, secrets, auth rules, exit codes, empty input, malformed files, deterministic output and absence of input mutation.

Now run the second team's file:

```sh
python app.py --input inputs/secondary.json
```

The unchanged validator applies its narrower mobile policy. Profile 0 passes; profile 1 has a disallowed host and excessive duration; profile 2 has an unused auth reference and a floating-point duration; profile 3 contains a secret in an unknown auth field. Totals are 4 profiles, 1 valid, 3 invalid, 5 errors and 1 warning, with exit 1.

Finally, run the truncated file:

```sh
python app.py --input inputs/malformed-input.txt
```

It produces a readable line/column error and exits 2. Complete reports, test output and exit statuses are saved in `evidence/`. The main submission report explains decisions, limitations and AI use. The core is deliberately kept as a standard-library CLI so a reviewer can run and inspect it without setup beyond Python.
