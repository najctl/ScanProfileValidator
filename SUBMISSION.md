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
| `primary-report.json` | One complete primary report, shared by all run methods. |
| `secondary-report.json` | One complete secondary report, shared by all run methods. |
| `tests.txt` | Saved output showing the existing 18 tests passed. |
| `malformed-error.txt` | One example of readable fatal-error handling. |
| `verification.json` | Consolidated Python, Docker and Compose execution records, report comparisons, environment details and file hashes. |

The validator calculates its results from the selected input. **It does not use the evidence files to obtain its answers, and normal runs do not create files in this folder.**

Docker and Compose produced reports identical to the two saved reports. Their commands, outcomes and comparisons are recorded in `verification.json`; duplicate copies of the same JSON reports are not included.

## 9. Implementation decisions and work log

**Priority:** complete the required validator, verify both supplied examples, and make execution reproducible. The optional Docker runner was added after the core was verified. A server, database and deployment were deferred because the assignment does not require them.

**Why Docker and Compose were added:** Docker supplies a consistent Python environment for reviewers who prefer containers. Compose stores the runtime options in one file, reducing the commands they need to remember. Both were added after the core validator was verified, as optional improvements to local use. They do not add a server, database, public deployment or new validation behavior. The README allows optional local developer-experience improvements and makes clear that the core alone can earn full marks.

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

Docker packages the same program with Python, so a reviewer can run it without installing Python locally. This is an optional convenience; it does not change the input files, rules or results.

**This is local execution, not public deployment.** No application port is exposed, no web service is started, and the image has not been published. Building may download the official Python base image; validation itself runs without container networking under the documented commands.

### Start Docker and build the image

Install Docker if needed, then start its engine. On Windows, start Docker Desktop and use Linux containers. Open a terminal in this project folder and run:

```powershell
docker build -t scan-profile-validator .
```

The first build may need an internet connection to download the Python base image. It also runs the existing **18 tests**. The build must succeed before you use the commands below.

### Run the supplied examples

```powershell
docker run --rm --network none --read-only scan-profile-validator --input inputs/primary.json
docker run --rm --network none --read-only scan-profile-validator --input inputs/secondary.json
```

The reports have the same totals as the Python commands. Both exit **1** because the supplied files contain deliberate errors. With no arguments, the container checks the primary input by default.

The options remove the container afterward (`--rm`), disable its network (`--network none`), and make its filesystem read-only (`--read-only`). No ports or real credentials are needed.

### Run the same tests in Docker

```powershell
docker run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --entrypoint python scan-profile-validator -m unittest discover -s tests -p "*_test.py" -v
```

Expect **18 tests passing**, with exit **0**. The temporary directory is needed because the existing tests create temporary JSON files; no new test cases were added.

For the malformed example:

```powershell
docker run --rm --network none --read-only scan-profile-validator --input inputs/malformed-input.txt
```

Expect the same readable error and exit **2**. In PowerShell, inspect `$LASTEXITCODE` immediately after each command.

### Use your own input file

Docker can read a folder you explicitly mount into it. If `my-profile.json` is in your current folder, this PowerShell command makes that folder available read-only at `/data`:

```powershell
docker run --rm --network none --read-only --mount "type=bind,source=$($PWD.Path),target=/data,readonly" scan-profile-validator --input /data/my-profile.json
```

The file must follow the same input structure, including its policy and profiles list. It is not rewritten.

### Verified Docker results

The image was built locally and the same 18 tests passed inside the container. Primary and secondary JSON reports were compared in full with the native reports and matched exactly. Help, default input, malformed input and the read-only host-file mount were also verified. The commands, outcomes, build result and full-report comparisons are recorded in the `docker` section of `evidence/verification.json`. The shared reports above avoid duplicate output files.

### Container decisions

The base image is pinned to a specific digest for repeatable builds. The process runs as non-root user `10001:10001`. Only the three source files, supplied inputs and existing test file enter the build context. No package installation, extra service, multi-stage compilation or public image publishing is required for this standard-library application.

Docker commands and their options follow the official [Dockerfile reference](https://docs.docker.com/reference/dockerfile/) and [container-run documentation](https://docs.docker.com/engine/containers/run/). Docker execution outcomes are consolidated in `evidence/verification.json`; native Python execution remains available independently.

## 12. Optional: shorter Docker commands with Compose

Compose reads `compose.yaml`, which stores the container settings so you do not have to repeat them in every command. It runs the same program and the same 18 tests. There is no database or extra running service.

Start Docker Desktop with Linux containers, then open a terminal in the project folder. Check that Compose is available:

```powershell
docker compose version
```

### Build and run the primary example in one command

```powershell
docker compose run --build --rm validator --input inputs/primary.json
```

Read that command as follows:

| Part | Meaning |
| --- | --- |
| `docker compose run` | Run a one-off command using the Compose configuration. |
| `--build` | Build the image before running it; unchanged build layers can be reused. |
| `--rm` | Remove the container after it finishes. |
| `validator` | The service name in `compose.yaml`; it identifies the application, not an input file. |
| `--input inputs/primary.json` | Tell the application which JSON file to check. |

On the first run, the image build includes the existing test suite. You may see build progress before the report. The primary report should contain **7 profiles, 2 valid, 5 invalid, 13 errors and 2 warnings**, with exit **1**. These are expected input-validation findings.

If you omit `--input`, the application uses `inputs/primary.json` by default. To select another file, keep the same service name and change the input argument, as shown below.

### Run the secondary example

```powershell
docker compose run --rm validator --input inputs/secondary.json
```

Expect the same secondary report and exit **1**.

### Run the existing tests

```powershell
docker compose run --rm --entrypoint python validator -m unittest discover -s tests -p "*_test.py" -v
```

Expect **18 tests passing** and exit **0**. These are the same test cases as the native Python suite, not additional cases.

To check malformed JSON:

```powershell
docker compose run --rm validator --input inputs/malformed-input.txt
```

Expect a readable error and exit **2**. Use `$LASTEXITCODE` immediately afterward in PowerShell to inspect the result.

### Save a report

Keep build output separate by building first, then redirecting a run's JSON output:

```powershell
docker compose build
docker compose run --rm validator --input inputs/primary.json > primary-report.json
```

The report is saved on your computer. A database is not needed to retain this output.

### What Compose configures

The container runs as user `10001:10001`, without a network, with a read-only root filesystem and a small writable temporary directory for the existing tests. Linux capabilities are dropped and privilege escalation is disabled. No host folders or Docker socket are mounted by default. `--rm` removes the container afterward; the built image remains available for reuse.

The build-and-run command, both full reports, the same 18 tests, malformed-input handling and runtime settings were verified locally. Results and runtime settings are recorded in the `compose` section of `evidence/verification.json`, with one shared JSON report per fixture. The configuration follows the official [Compose service reference](https://docs.docker.com/reference/compose-file/services/) and [one-off command documentation](https://docs.docker.com/reference/cli/docker/compose/run/).
