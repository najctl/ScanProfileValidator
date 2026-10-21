# Scan profile config validator with path-precise diagnostics

**Reviewer quick start:** [Submission report and run guide](SUBMISSION.md) · [Written walkthrough](WALKTHROUGH.md) · [Recorded verification](evidence/verification.json)

The implementation, tests, supplied inputs and submission documents are included in this directory. The assessment instructions and acceptance criteria follow below.

This is one Software Engineer Intern assessment with a **24-hour** window. Your recruiter assigns one exercise from the bank. Your 24 hours start when you click **Start** on the link in your invitation email; the exercise zip becomes available at that moment. Send your submission back within 24 hours of clicking Start. You are not expected to work for the full 24 hours: organize your own working time and breaks within the window. There are no surprise messages or overnight availability requirements, and hours worked are not scored. Follow-through and verification matter more than hours or volume.

Teams on the fictional North scanning platform submit scan profiles as JSON. A bad profile is noticed only hours later, when its scan fails, and some profiles contain pasted credentials. Build a reusable validator CLI that reports every problem with a precise JSON path before submission, separates errors from warnings, and never repeats a secret.

All companies, tenants, assets and product behavior here are **fictional assessment facts**. The supplied fixtures are the authoritative universe. Outside research is optional and cannot affect marks. Do not contact real systems, send real messages, publish, or use production credentials.

## Supplied inputs and setup

You need basic Python, JSON, CLI use, tests, and familiarity with schema validation, URL parsing and diagnostics. Python **3.10 or later**, its standard library, and any local editor are sufficient; no packages, accounts, paid tools, web access or company framework are needed.

- [Validator CLI](app.py): argument parsing, safe JSON loading, and reusable profile validation.
- [Primary fixture](inputs/primary.json): main cases, including deliberate inconsistencies.
- [Second fixture](inputs/secondary.json): another team's profiles and policy; use it to demonstrate reuse.
- [Malformed input](inputs/malformed-input.txt): deliberately truncated JSON, despite its .txt extension; use for error handling.
- [Automated checks](tests/app_test.py): infrastructure, feature acceptance, boundary, and regression tests.

`demo_tok_` and `DEMO-KEY-` values are fake, nonfunctional secrets.

From the exported `candidate/` directory:

```sh
python --version
python app.py --help
python -m unittest discover -s tests -p '*_test.py' -v
python app.py --input inputs/primary.json
```

The validator is implemented. The test suite includes feature assertions and the original help/file-error checks. The primary command prints a JSON report and exits **1**, because its intentional invalid profiles are detected. See [SUBMISSION.md](SUBMISSION.md) for the run guide, decisions, AI-use note, and text walkthrough. Python 3.10+ is required; no packages are needed. On systems where the interpreter is named python3, substitute python3 for python in these commands.

## Core task and observable acceptance criteria

Build a usable feature implementing the following contract. Use JSON on stdout for successful runs, readable diagnostics on stderr for fatal errors, and the documented exit codes. Explain any assumptions without silently changing the rules.

- Input is an object with `policy` (`allowed_suffixes`: strings starting with `.`; `secret_prefixes`: nonempty strings) and a `profiles` array of objects. Anything else, an unreadable file or malformed JSON exits 2 with a readable error and no stdout.
- Each diagnostic is `{"path", "code", "message"}` with a zero-based JSON path such as `$.profiles[2].auth.token_ref` or `$.profiles[5].exclude_paths[1]`. Error codes: `missing`, `type` (wrong JSON type; no further checks on that field), `invalid` (breaks a format, range or allowed-value rule), `duplicate`, `not_allowed`, `secret`. A profile key other than the six below, or an `auth` key other than `type`, `token_ref`, `recording_id`, is an `unknown_field` warning. Report every problem, not just the first.
- Required profile fields: `name` matches `^[a-z][a-z0-9-]{2,39}$` and is unique ignoring case (a later repeat gets `duplicate`, plus any `invalid`). `target` is an `https` URL whose parsed host, lowercased, ends with one of `allowed_suffixes`. `schedule` is exactly `daily HH:MM` or `weekly DAY HH:MM`, with DAY one of `Mon Tue Wed Thu Fri Sat Sun` and a two-digit 24-hour time `00:00`–`23:59`. `max_duration_minutes` is an integer from 5 to 240; booleans and numbers with a decimal point or exponent (`45.0`) are `type` errors.
- `auth` is required; its `type` is `none`, `bearer` or `recorded`; if missing or wrong, skip the other auth checks. `bearer` requires `token_ref`, an environment variable name matching `^[A-Z][A-Z0-9_]{2,63}$`. `recorded` requires `recording_id` matching `^rec-[0-9]{4}$`. A `token_ref` or `recording_id` the type does not use is `not_allowed`. Optional `exclude_paths` holds strings starting with `/`; an exact repeat is `duplicate`.
- Any string at any depth of a profile, unknown fields included, that starts with a `secret_prefixes` entry is a `secret` error, and that path gets no other error. No output may contain the secret value.
- Output `profiles` in input order, each with `index`, `name` (or `null` if not a string), `valid` (no errors; warnings do not count), `errors` and `warnings`, each sorted by path then code as plain strings; and `summary` with `profiles, valid, invalid, errors, warnings`. Exit 0 when all profiles are valid, **1** when any is invalid (still printing the report), 2 when fatal. The implemented CLI returns exit 1 for invalid profiles.
- Output is deterministic and the input is never changed. Empty `profiles` gives zero counts and exit 0. Each fixture carries its own policy.

Primary: 7 profiles, 2 valid, 5 invalid, 13 errors, 2 warnings, exit 1. Per profile (index: errors/warnings): 0: 0/0, 1: 0/1, 2: 4/0, 3: 1/0, 4: 2/0, 5: 3/0, 6: 3/1. Add tests for case-insensitive duplicates, a boolean duration, host matching, a redacted secret, exit codes 0/1/2, an empty batch and malformed input. Secondary: run the validator unchanged and reconcile every profile.

Add meaningful automated checks that test results and errors, not just that code runs. Include at least one boundary case you construct, and one failing case you fix or a validation that causes a refinement. A clear, tested core earns full marks. Optional stretch: improve the local developer experience or add a useful extra test; no stretch is necessary. A web service, full framework, database, public deployment, or large architecture is outside the core scope.

After implementing the core, use these exact local verification runs. Both fixture invocations print their reports and exit 1 because they contain deliberate invalid profiles.

```sh
python app.py --input inputs/primary.json
python app.py --input inputs/secondary.json
```

## Time and AI use

Plan your own time within the 24-hour window. Prioritize the core contract and leave time for verification instead of adding features.

**AI is allowed and encouraged** for coding, explanation, test generation, critique and optional research. Tool choice is not graded. No AI tool is provided; you may use any AI tool you already have, and no purchase is required. Free/offline tools and completing the exercise without AI are supported. Check AI output against the rules, input profiles and executed tests. Submit a short AI-use note with one concrete accepted, corrected or rejected output and how you checked it; if you did not use AI, state that. Do not invent an AI failure or share complete prompt histories, private account access, or secrets.

## Submission

Submit an archive or repository containing runnable source, tests, the supplied inputs, and:

1. A short run guide with exact commands for both fixtures and the meaningful checks; include representative outputs or assertions with profile index/path references.
2. A concise decision/work log: priorities and what you deferred; one obstacle and response; one validation/refinement; known limits and next step. Cite profile indexes, names or JSON paths as evidence.
3. The AI-use note described above.
4. A 3–5 minute walkthrough recording **or equivalent accessible text** explaining the core workflow, one edge case, and evidence of execution.

You do not need a public repository, deployment, PDF or proprietary tools. Document incomplete behavior honestly. Do not submit only a design or report: the runnable feature and reproducible tests are the primary deliverables.

Published scoring: **usable result 40, accuracy/verification 25, prioritization 20, communication/handoff 15**. Full marks are available on the core alone. Tool choice, AI-detector judgments, prose polish, hours worked and sheer output volume are not scored.

