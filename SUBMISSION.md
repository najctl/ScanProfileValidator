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

The README preserves the original exercise text, including descriptions of the unfinished starter. This guide describes the completed submission.

You can run the same validator in two ways: directly with Python (sections 2–6), or locally through Docker Compose (section 12). Choose one route; you do not need both. The rules, input files, reports and 18-test suite are the same.

## 1. Open the project

Extract the submission ZIP, then open a terminal inside the extracted project folder—the folder containing `app.py`.

The project contains:

```text
app.py             Starts the command-line program
validator.py       Checks the validation rules
diagnostics.py     Formats paths, redacts secrets, and builds totals
Dockerfile         Optional container build and runner
.dockerignore      Limits the files sent to the Docker build
compose.yaml       Shorter optional Docker commands

inputs/            Example files supplied with the assignment
tests/             Automated checks for the program
evidence/          Saved results from executed commands

README.md          The company's assignment
SUBMISSION.md      This guide and the implementation notes
WALKTHROUGH.md     A worked example showing the program in use
```

Keep the three Python files together.

## 2. Check Python

For the direct Python commands below, Python **3.10 or later** is required. No additional packages are needed. If you prefer to use Docker instead of a local Python installation, go to **section 12** for the shorter Compose commands, or **section 11** for direct Docker commands.

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

These are **18 test methods**, with several inputs checked inside some methods. They test the program; they are separate from the profiles in a report. `OK` means they passed; elapsed time varies.

| Existing test | Cases checked and expected result |
| --- | --- |
| Help | Show the input option and exit `0`. |
| Missing or broken file | Show a readable error, no JSON report, and exit `2`. |
| Primary example | Match every error path/code, warning counts and totals: 13 errors, 2 warnings; exit `1`. |
| Secondary example | Apply its own policy; match error paths/codes and totals: 5 errors, 1 warning; exit `1`. |
| Duration | Accept `5` and `240`; reject `4` and `241`. Boolean, decimal, string and null values produce type errors. |
| Duplicate names | `api-nightly` followed by `API-Nightly`: the second gets duplicate and uppercase-format errors. |
| Website host | Accept an allowed uppercase host with a numeric port; reject HTTP, misleading host text, a disallowed suffix and a malformed port. |
| Secrets in nested data | Hide secrets in names, nested values and unknown field names, including quotes, backslashes and Unicode. One secret error per location; input unchanged. |
| Secrets through the CLI | Neither output stream reveals the tested secrets; report paths hide them too. |
| Diagnostic codes during redaction | Hide the secret name while preserving the required `type` error code. |
| Redaction marker | Keep `[REDACTED]` intact even when another secret could match part of that marker. |
| Missing fields and auth types | Report missing fields or wrong auth types; skip dependent auth checks when the auth type is missing or invalid. |
| Auth references | Reject missing or malformed references and fields unused by the chosen auth type; accept `rec-0001`. |
| Schedule | Accept midnight and Sunday `23:59`; reject `24:00`, `12:60`, a one-digit hour, lowercase day and trailing newline. |
| Excluded paths and warnings | Reject missing leading slash, duplicates and wrong types. An unknown field alone leaves the profile valid. |
| Repeatability | Repeated validation returns identical results and leaves the input unchanged. |
| Valid and empty batches | Exit `0`; an empty batch returns empty results and zero totals. |
| Invalid input structure | Reject the tested wrong root, missing policy, bad suffix and non-object profile; no report, exit `2`. |

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
| `primary-report.json` | One complete primary report, shared by all run methods. |
| `secondary-report.json` | One complete secondary report, shared by all run methods. |
| `tests.txt` | Saved output showing the existing 18 tests passed. |
| `malformed-error.txt` | One example of readable fatal-error handling. |
| `verification.json` | Consolidated Python, Docker and Compose execution records, report comparisons, environment details and file hashes. |

The validator calculates its results from the selected input. **It does not use the evidence files to obtain its answers, and normal runs do not create files in this folder.**

Docker and Compose produced reports identical to the two saved reports. Their commands, outcomes and comparisons are recorded in `verification.json`; duplicate copies of the same JSON reports are not included.

## 9. Implementation decisions and work log

**Priority:** complete the required validator, verify both supplied examples, and make execution reproducible. The optional Docker runner was added after the core was verified. A server, database and deployment were deferred because the assignment does not require them.

**Why containers:** Docker provides a consistent Python environment; Compose saves the runtime settings. Both are optional local conveniences, added after core verification. The README permits this stretch and awards full marks on the core alone.

**Code organization:** `app.py` handles arguments, files, output, and exit codes. `validator.py` applies the rules. `diagnostics.py` handles paths, redaction, sorting, and totals. This keeps validation reusable without command-line dependencies.

**Obstacle:** Python treats booleans as integers in some type checks. Exact type checking prevents `true` from being accepted as a duration. Primary profile 2 and the duration tests verify this behavior.

**Refinement:** an early redaction implementation could overwrite diagnostic codes or rewrite its replacement marker. Two regression checks reproduced those problems. Redaction was corrected, and both checks now pass within the 18-test suite.

**Further review:** nested secret detection uses an explicit stack to avoid recursion failures. A later review found that an error or warning location could reveal a secret used as an unknown field name, especially if it contained a quote, backslash, newline or non-ASCII character. Secret-looking unknown names are now detected, and each path component is redacted before being escaped for display. The input stays unchanged. These cases were added inside existing tests, so the suite still has 18 test methods. The module imports and execution from another directory were also checked.

### Assumptions and limitations

- Empty policy arrays are accepted because no minimum length is specified.
- Hostnames are lowercased; suffixes are matched literally. URL syntax checking also rejects malformed ports and whitespace.
- Unknown profile and auth fields receive warnings. Unknown root and policy fields are ignored.
- Secret values and secret-looking unknown field names are hidden in displayed names and diagnostic paths. Path components are checked before JSON escaping, so quotes, backslashes and Unicode do not bypass redaction. A secret key and value at the same path produce one secret error. Fixed schema field names are protocol labels; required report keys and diagnostic codes remain unchanged. Policies that classify protocol words as secrets create a conflict, documented here explicitly.
- Detection follows the configured prefix rule. It is not a general credential detector.
- JSON parsing remains subject to interpreter resource limits. There is no explicit file-size limit; adding a documented limit would be the next step for larger-input use cases.

## 10. AI-use note

- I worked through the requirements and expected results, then chose the structure for the solution: separate command-line handling, validation rules and diagnostic formatting, with no external dependencies.
- I used Codex to generate and revise Python code for that structure, draft test cases and handle repetitive documentation work. I directed those tasks through focused instructions and requested changes when the output did not meet the intended behavior or presentation.
- I checked the generated work against the assignment by running the unit suite and both supplied fixtures locally. One concrete correction involved secret redaction: the generated replacement logic could overwrite the error code `type` and alter its own redaction marker. I requested a fix; the regression checks failed before correction and passed afterward. A later review also found a leak through unusual field names in diagnostic paths. I requested that correction, and the existing secret tests were extended to cover it while keeping 18 test methods.
- I requested the optional Docker and Compose workflows and used Codex to prepare them: a pinned Python image, a non-root user and a limited build context, while keeping the application standard-library-only.
- AI supported the implementation; I remained responsible for the approach, review, accepted changes and final verification. The delivered solution has 18 passing test methods and reproduces the required primary results.

## 11. Optional: run with Docker

For the shorter container route, use **section 12**. Direct Docker commands are provided here for reviewers who prefer them.

Start the Docker engine (Docker Desktop with Linux containers on Windows). From the project folder, build the image:

```powershell
docker build -t scan-profile-validator .
```

The build runs the same 18 tests and may download the pinned Python base image. After it succeeds:

```powershell
docker run --rm --network none --read-only scan-profile-validator --input inputs/primary.json
docker run --rm --network none --read-only scan-profile-validator --input inputs/secondary.json
```

Both return the reports in section 7 and exit `1`. Omitting the arguments selects primary by default.

Run the existing suite, allowing temporary files for its test inputs:

```powershell
docker run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --entrypoint python scan-profile-validator -m unittest discover -s tests -p "*_test.py" -v
```

Expect 18 passing tests and exit `0`. Check malformed input with:

```powershell
docker run --rm --network none --read-only scan-profile-validator --input inputs/malformed-input.txt
```

Expect a readable error and exit `2`. In PowerShell, inspect `$LASTEXITCODE` immediately after a command.

To check your own `my-profile.json` in the current folder, mount that folder read-only:

```powershell
docker run --rm --network none --read-only --mount "type=bind,source=$($PWD.Path),target=/data,readonly" scan-profile-validator --input /data/my-profile.json
```

The file needs the same policy/profiles structure. The pinned image runs as non-root user `10001:10001`; the build context includes only source, supplied inputs and tests. Validation runs without networking under these commands. This is local execution with no exposed ports or published service.

Recorded checks cover the build, tests, full report equality with Python, help, default input, malformed input and the host-file mount. See the `docker` section of `evidence/verification.json`.

## 12. Optional: shorter Docker commands with Compose

Compose stores the container options in `compose.yaml`. Start Docker Desktop with Linux containers, open the project folder in a terminal, then check availability:

```powershell
docker compose version
```

Build and run primary:

```powershell
docker compose run --build --rm validator --input inputs/primary.json
```

`validator` names the application service; `--input` selects the file. `--build` builds the image first, including the 18 tests; `--rm` removes the container afterward. Omitting `--input` selects primary.

Run secondary and the same test suite:

```powershell
docker compose run --rm validator --input inputs/secondary.json
docker compose run --rm --entrypoint python validator -m unittest discover -s tests -p "*_test.py" -v
```

The fixture reports match section 7 and exit `1`; all 18 tests should pass with exit `0`.

Check malformed input (readable error, exit `2`):

```powershell
docker compose run --rm validator --input inputs/malformed-input.txt
```

Use `$LASTEXITCODE` immediately afterward to inspect a command's result.

To save a report on your computer, build separately before redirecting the JSON output:

```powershell
docker compose build
docker compose run --rm validator --input inputs/primary.json > primary-report.json
```

Compose uses a non-root user, no network, a read-only root filesystem and a small temporary directory for tests. It drops Linux capabilities, disables privilege escalation, and mounts no host folders or Docker socket by default. No database or public deployment is involved.

The build-and-run workflow, reports, tests, malformed input and runtime settings were verified; see the `compose` section of `evidence/verification.json`.
