# Project handoff for another AI or developer

Prepared on 22 October 2026. This document preserves the useful context from a long conversation. It is a private continuity document, not part of the recruiter submission. It summarizes the work and decisions rather than reproducing every message verbatim.

## 1. Read this first

The user completed a Python internship assessment: **Scan profile config validator with path-precise diagnostics**. The project is ready for submission according to the checks described below. The user said they were submitting; successful upload has not been independently confirmed.

The latest request was to create this handoff because this is a friend's account and the user wants to continue with another AI. Do not assume the next AI has the source files simply because it has this document. To inspect or change the implementation, it needs the actual project or final ZIP too.

Current project location:

```text
C:\Users\HP\Desktop\9raya\candidate
```

Final submission archive:

```text
C:\Users\HP\Desktop\9raya\candidate\scan-profile-validator-submission.zip
```

At the last packaging check, the archive was **32,491 bytes**, contained **20 files**, and matched the current project files. It excludes this handoff, the MP4 and SRT files, Git metadata, caches, dependencies and build folders.

**Do not change the submitted version merely to make it look different.** There was no known remaining blocking issue at the end of the review. Do not promise a perfect score or guaranteed hiring outcome.

## 2. How to work with this user

- Use simple, direct English. The user knows Python but wants the purpose and behavior explained concretely.
- Give a small example when explaining a bug or rule. Avoid long abstract explanations and unexplained terms.
- Be concise for normal questions. Give detailed steps when explicitly requested.
- If the user is asking a question, answer it; do not silently interpret it as permission to edit files.
- Explain proposed changes before making them when approval is requested. Respect the scope of any approval already given.
- Do not change the original company `README.md` or supplied input files.
- Keep **18 test methods**. The user strongly opposed increasing the method count from 18 to 22. Real regression cases were added inside existing methods instead.
- Preserve the approved submission table layout: each issue is on a separate visual line using `<br>`. Do not cram several unrelated errors into one semicolon-separated paragraph.
- Preserve the approved documentation structure unless a specific change is requested.
- Do not add extra duplicate evidence reports for Python, Docker and Compose. One report per fixture is enough when the outputs match.
- Never say something was verified unless it was actually checked. Distinguish recorded evidence, current checks and untested assumptions.
- The user does not want unsolicited wording about AI explaining the assignment to them. The required AI-use note describes their direction and review of AI-assisted work. Do not fabricate authorship, tests or decisions.
- The user removed the video narration bullet from the AI-use note. They explicitly accepted the other mentions of AI narration elsewhere. Do not restore that removed bullet.

## 3. What the assignment is actually asking for

Build a reusable command-line program that checks JSON scan settings before they are submitted to a fictional scanning platform.

It **does not visit websites, scan websites, log in to websites, or schedule real scans**. A target URL is only configuration data being validated.

Input has two main parts:

```json
{
  "policy": {
    "allowed_suffixes": [".example.test"],
    "secret_prefixes": ["demo_tok_"]
  },
  "profiles": []
}
```

Each profile describes a scan's name, target URL, schedule, authentication, maximum duration and optional excluded paths. The program reports every detected problem, including its exact location, and distinguishes errors from warnings.

The supplied fixtures are authoritative. Outside research cannot change the assessment rules. They use fictional assets and fake secrets.

### Input and validation rules

- Root must be an object, `policy` an object, and `profiles` an array of objects.
- `policy.allowed_suffixes` is an array of strings starting with `.`.
- `policy.secret_prefixes` is an array of nonempty strings.
- Required `name`: full match of `[a-z][a-z0-9-]{2,39}`. Names must be unique ignoring case. A later repeated name gets `duplicate`, plus `invalid` if its format is also wrong.
- Required `target`: HTTPS URL whose parsed, lowercased hostname ends with one of that input's allowed suffixes. An allowed-looking substring elsewhere in the URL is insufficient.
- Required `schedule`: exactly `daily HH:MM` or `weekly DAY HH:MM`. DAY is `Mon Tue Wed Thu Fri Sat Sun`; hour is two digits from `00` to `23`, minute from `00` to `59`.
- Required `max_duration_minutes`: an integer from **5 through 240**, inclusive. JSON booleans, floating-point values and exponent-form numbers are not acceptable integers.
- Required `auth`: object with `type` equal to `none`, `bearer` or `recorded`. Skip dependent auth checks if the type is missing, wrongly typed or invalid.
- Bearer auth requires `token_ref` matching `[A-Z][A-Z0-9_]{2,63}`.
- Recorded auth requires `recording_id` matching `rec-[0-9]{4}`.
- A reference field unused by the chosen auth type is `not_allowed`.
- Optional `exclude_paths`: array of strings starting with `/`; repeated exact entries get `duplicate`.
- Unknown profile keys and unknown auth keys get `unknown_field` warnings.
- A string at any depth of a profile beginning with a configured secret prefix gets a `secret` error. That path gets no other error. Output must not repeat the detected secret value.
- Input must remain unchanged. Repeated validation must give deterministic results. Each input uses its own policy.

### Required output and exit codes

Each profile result includes `index`, `name` (or null for a non-string name), `valid`, `errors` and `warnings`. Profiles stay in input order. Diagnostics contain `path`, `code`, `message` and are sorted by path then code as ordinary strings.

Paths are zero-based, for example:

```text
$.profiles[2].max_duration_minutes
```

This means the duration field of the third profile.

Error codes are `missing`, `type`, `invalid`, `duplicate`, `not_allowed`, `secret`. Wrong types stop further checks on that field. Warnings do not invalidate a profile.

The report also includes totals: `profiles`, `valid`, `invalid`, `errors`, `warnings`.

| Exit | Meaning |
| ---: | --- |
| 0 | All profiles valid, including an empty batch. |
| 1 | Report produced, but at least one profile invalid. |
| 2 | Fatal input/read/structure error; readable stderr, no JSON stdout. |

The starter originally returned exit 3 for the unimplemented feature. That placeholder is intentionally replaced in the finished program.

## 4. Expected fixture results

| Fixture | Profiles | Valid | Invalid | Errors | Warnings | Exit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Primary | 7 | 2 | 5 | 13 | 2 | 1 |
| Secondary | 4 | 1 | 3 | 5 | 1 | 1 |

Primary expectations are explicitly stated in the original README. Secondary expectations were reconciled profile by profile against its policy and the rules; they are not a second totals table supplied by the README.

### Primary details

| Index / name | Errors | Warnings |
| --- | --- | --- |
| 0 / api-nightly | None | None |
| 1 / portal-weekly | None | `owner`: unknown_field |
| 2 / API-Nightly | `max_duration_minutes`: type<br>`name`: duplicate<br>`name`: invalid<br>`schedule`: invalid | None |
| 3 / billing-scan | `auth.token_ref`: secret | None |
| 4 / partner-export | `auth.token_ref`: not_allowed<br>`target`: invalid | None |
| 5 / search-crawl | `exclude_paths[1]`: invalid<br>`exclude_paths[2]`: duplicate<br>`target`: invalid | None |
| 6 / docs-preview | `api_key`: secret<br>`auth.token_ref`: missing<br>`schedule`: missing | `api_key`: unknown_field |

Example explanation for profile 2: uppercase letters break the name format; its name repeats `api-nightly` ignoring case; `daily 7:30` needs `07:30`; duration `true` is a boolean, not an integer.

### Secondary details

| Index / name | Errors | Warnings |
| --- | --- | --- |
| 0 / mobile-api-daily | None | None |
| 1 / mobile-web-weekly | `max_duration_minutes`: invalid<br>`target`: invalid | None |
| 2 / mobile-push | `auth.recording_id`: not_allowed<br>`max_duration_minutes`: type | None |
| 3 / mobile-legacy | `auth.token`: secret | `auth.token`: unknown_field |

## 5. Final source structure

| File | Responsibility |
| --- | --- |
| `app.py` | Parse CLI arguments, load UTF-8 JSON, call validation, print report, handle fatal errors and exit codes. |
| `validator.py` | Apply the validation rules without filesystem or CLI dependencies; do not mutate input. |
| `diagnostics.py` | Construct paths, redact secret text, sort diagnostics and calculate totals. |
| `tests/app_test.py` | Existing suite, currently 18 test methods. |
| `Dockerfile` | Optional pinned Python container; runs tests during build. |
| `compose.yaml` | Optional saved container settings and shorter commands. |
| `.dockerignore` | Restricts build context to source, supplied inputs and tests. |
| `.gitignore` | Excludes Python caches and similar local files. |

The user explicitly accepted splitting the code as long as it works and preserves behavior. The three Python modules must stay together. The application uses only the Python standard library.

The CLI defaults to `inputs/primary.json` when `--input` is omitted. Its JSON parser rejects non-finite values such as NaN and Infinity. Read failures, malformed JSON and excessive parser nesting produce safe fatal errors.

## 6. Important fixes and why they were needed

These were implementation corrections to follow the company rules, not edits to those rules or fixtures.

### Boolean duration

Python considers booleans instances of integers in some checks. The validator uses exact type checking, so JSON `true` cannot pass as a duration. Both duration endpoints are tested.

### Redaction must preserve report codes and its marker

An earlier replacement approach could alter a required diagnostic code such as `type`, or replace text inside the inserted `[REDACTED]` marker. Regression checks reproduced the issues. Redaction now protects display text while preserving protocol keys/codes and performs a single substitution pass.

### Secret text inside unusual field names

Example:

```json
{"demo_tok_private": "some value"}
```

A warning path that literally repeated that key could expose a secret even though the program did not print its value. Unknown keys and nested data are checked too. Path components are redacted before JSON escaping, covering quotes, backslashes, newlines and Unicode. A secret key and value at one location produce one secret error there.

Existing test methods were extended; the shipped method count remains 18. An explicit stack handles deeply nested unknown data without recursive secret traversal.

### Final duplicate-name fix

Example:

```text
First profile name:  demo_tok_same
Later profile name:  DEMO_TOK_SAME
```

The first name is detected as a secret and hidden in displayed output. Previously, it was also accidentally skipped in the internal set of earlier names. The later uppercase name could therefore miss a duplicate error.

The fix remembers every earlier string name internally even if secret precedence suppresses its displayed validation errors. Later comparisons still ignore case. Secret display stays redacted.

This is a general algorithmic fix, not a special case hard-coded for these names. The fixed names exist only in the regression example. The existing duplicate test failed before the fix and passed afterward. No new test method was added.

Both supplied fixture reports remained unchanged by this correction.

## 7. Tests and verification

The initial four company smoke checks were infrastructure checks, not feature acceptance tests. The README explicitly asks to replace the unfinished-feature assertion with feature assertions and retain help/file-error behavior. The final suite preserves those behaviors and adds meaningful feature coverage.

The 18 methods cover:

1. Help output.
2. Missing files and malformed JSON.
3. Exact primary diagnostics and totals.
4. Secondary policy reuse and diagnostics.
5. Duration boundaries and types.
6. Case-insensitive duplicate names, including earlier secret names.
7. Parsed hostname matching and misleading URLs.
8. Nested secrets, secret names and unusual object keys.
9. Secret redaction through the CLI.
10. Preserving required diagnostic codes during redaction.
11. Preserving the redaction marker.
12. Missing fields, wrong types and skipped dependent auth checks.
13. Auth reference formats and unused fields.
14. Schedule boundaries and formatting.
15. Excluded paths and warning-only validity.
16. Determinism and no input mutation.
17. Valid and empty batches returning exit 0.
18. Invalid envelopes returning exit 2.

There can be multiple cases within one method. Eighteen methods does not mean only eighteen input values were checked. This is `unittest`, not a pytest dependency.

Final review also used temporary audit scripts outside the submission to check 16 requirement groups, exact original-file hashes, Python 3.10 syntax compatibility, documentation links, and clean archive extraction. These audit scripts were not extra shipped test methods.

Recorded checks include:

- 18 tests passing natively and in Docker/Compose.
- Complete fixture reports equal across Python, Docker and Compose, not merely equal totals.
- Correct help, default input, malformed-input behavior and exit codes.
- Imports and invocation from another working directory using explicit paths.
- Determinism across hash seeds and unchanged input objects/files.
- Fresh Docker build and tests from the extracted submission ZIP.
- Runtime container settings and read-only host input mount.
- ZIP integrity, no prohibited folders, included file hashes, local documentation links and size below the portal limit.

The saved native test run took **3.831 seconds**. Other runs took different times, including roughly 6–7 seconds in containers. This varies with environment and is not a correctness requirement. Do not confuse test-suite duration with the validator's own runtime.

No tests were rerun merely because the final edit changed documentation and packaging; source and test hashes were checked against the tested implementation.

## 8. Run commands

Open a terminal in the extracted directory containing `app.py`.

Python **3.10 or later**, no external packages:

```powershell
python --version
python app.py --help
python app.py --input inputs/primary.json
python app.py --input inputs/secondary.json
python -m unittest discover -s tests -p "*_test.py" -v
python app.py --input inputs/malformed-input.txt
```

On systems naming the interpreter `python3`, replace `python` with `python3`. In PowerShell, inspect `$LASTEXITCODE` immediately after a command. A fixture returning exit 1 is expected because those inputs deliberately contain errors.

Optional Docker Compose, with Docker engine running in Linux-container mode:

```powershell
docker compose run --build --rm validator --input inputs/primary.json
docker compose run --rm validator --input inputs/secondary.json
docker compose run --rm --entrypoint python validator -m unittest discover -s tests -p "*_test.py" -v
docker compose run --rm validator --input inputs/malformed-input.txt
```

`validator` is the Compose service name. `--rm` removes the stopped container, not its image. Results print to the terminal unless redirected.

To save output, build separately before redirecting:

```powershell
docker compose build
docker compose run --rm validator --input inputs/primary.json > primary-report.json
```

Direct Docker commands and a read-only input mount example are documented in `SUBMISSION.md`.

### Container choices

The base is pinned to:

```text
python:3.13-slim@sha256:6771159cd4fa5d9bba1258caf0b82e6b73458c694d178ad97c5e925c2d0e1a91
```

Compose uses UID/GID `10001:10001`, no network, a read-only root filesystem, dropped Linux capabilities, no privilege escalation and a 16 MB temporary `/tmp` for tests. No ports, database or public deployment are involved. The first build may need internet to obtain the base image.

Docker is an optional local convenience after core completion. It is not required for a reviewer who has Python. SQLite, a web server and deployment were discussed but not added because they were outside the core task.

## 9. Documentation and evidence

- `README.md`: untouched company exercise, including starter descriptions that intentionally describe the unfinished original state.
- `SUBMISSION.md`: start-here run guide, results, test coverage table, decisions, limits, AI-use note and optional container commands.
- `WALKTHROUGH.md`: follows one complete example from input to diagnostics, explains one edge case and how to verify results.
- `WALKTHROUGH_LINK.md`: external video link.

`SUBMISSION.md` is longer than ideal for the README's request for concise notes, but is clearly organized. The recommendation at the end was to submit the verified version instead of attempting a rushed rewrite. Do not describe its length as a proven reason for rejection.

Exactly five evidence files are retained:

| File | Purpose |
| --- | --- |
| `evidence/primary-report.json` | Canonical primary output. |
| `evidence/secondary-report.json` | Canonical secondary output. |
| `evidence/tests.txt` | Saved 18-test passing output. |
| `evidence/malformed-error.txt` | Saved readable fatal error. |
| `evidence/verification.json` | Execution commands, environments, comparisons, hashes and review metadata. |

`verification.json` is a record of how results were checked. It is not application input, a dependency, or something the validator uses to produce answers. Its hashes help detect changes to files. Normal program runs do not append evidence files automatically.

Earlier duplicated Docker/Compose reports were consolidated. Do not bring back separate identical copies for every runtime.

### AI-use wording decisions

The original README requires a short AI-use note with a concrete accepted/corrected/rejected AI output and how it was checked. The final note describes the user's requirements work, structure choices, directed code generation, review, fixture runs and regression corrections.

The user removed the bullet specifically describing AI narration/editing from that note. The project AI-use note itself remains. AI narration is still mentioned near the video links and in verification metadata, and the user said those remaining mentions are okay. Do not assume they requested removing all AI disclosure.

## 10. Video and submission portal rules

Final walkthrough link:

https://drive.google.com/file/d/14yB7qCmOp86NEQnSCa3YB9cPjIzAUFSJ/view?usp=sharing

The final video is **2 minutes 54 seconds**, with male AI narration and visible English captions. A written walkthrough is supplied because the README accepts a **3–5 minute recording OR equivalent accessible text**. The short companion video is not the only walkthrough deliverable.

Video history: the user recorded a longer demonstration and struggled with reading/speaking. Captions were corrected, offline male neural narration was generated, and an initial timing mismatch was corrected by aligning narration to screen actions with edits and screen holds. The selected final version is the synchronized version, not an earlier rough version.

Local final copy:

```text
C:\Users\HP\Desktop\9raya\candidate\WALKTHROUGH.mp4
```

Another copy was generated at:

```text
C:\Users\HP\.codex\visualizations\2026\10\21\01a15e67-fde1-7520-b424-3325ffaa0502\video-subtitles\Video-Project-synced-male-voice.mp4
```

The final video is 13,498,006 bytes. The local SRT is editable source; subtitles are already visible in the final MP4. The user uploaded only the MP4 to Drive.

The portal adds requirements beyond the exercise README:

- Upload a single `.zip`, maximum **5 MB**.
- Only one submission is permitted.
- Include a link to a recorded walkthrough, **not the video file**.
- Exclude dependency and build folders such as `node_modules`, `.venv`, `target`, `.gradle`, `build`, `bin`, `obj`.

An earlier archive included the video because the user had requested it before providing these portal rules. It was about 13.13 MB and was replaced. **Do not submit that older archive.** The final ZIP includes neither MP4 nor SRT, only the link documents.

The Drive preview was checked without an authenticated session: HTTP 200, title `WALKTHROUGH.mp4 - Google Drive`, expected 13,498,006-byte size, no sign-in/access-request page. Browser playback could not be directly tested by the agent. The user then explicitly confirmed the link works.

Do not change Drive permissions or upload anything externally without the user's authorization. Keep the link accessible to anyone with the link as a viewer.

## 11. Final ZIP contents

All entries are under `scan-profile-validator/`:

```text
app.py
validator.py
diagnostics.py
README.md
SUBMISSION.md
WALKTHROUGH.md
WALKTHROUGH_LINK.md
Dockerfile
compose.yaml
.dockerignore
.gitignore
tests/app_test.py
inputs/primary.json
inputs/secondary.json
inputs/malformed-input.txt
evidence/tests.txt
evidence/primary-report.json
evidence/secondary-report.json
evidence/malformed-error.txt
evidence/verification.json
```

The latest user-edited `SUBMISSION.md` was copied into the ZIP and packaged hashes were refreshed. All 20 archive entries were compared byte-for-byte with their workspace counterparts at the last packaging check.

This handoff must stay outside the recruiter ZIP. Local videos, SRT files and audit scripts can exist outside the ZIP; their presence on the user's PC is not a submission requirement.

If future edits are made, update the archive deliberately and refresh `evidence/verification.json` file hashes. Otherwise the ZIP can silently retain older content. Do not blindly zip the entire working directory.

## 12. Known assumptions and limits

- Empty policy arrays are accepted; the README specifies no minimum length.
- Hostnames are lowercased, suffix matching is literal, and malformed ports/whitespace are rejected.
- Unknown root/policy fields are ignored; unknown profile/auth fields produce warnings.
- Secret detection follows configured prefixes, not a general credential classifier.
- Fixed report schema labels/codes are preserved. Pathological policies classifying protocol words or the redaction marker as secret text create conflicting requirements; this is documented, not silently claimed solved for every imaginable policy.
- JSON parsing remains subject to interpreter resource limits; there is no explicit input-size limit. A documented size limit is a possible next step.
- Python 3.10 syntax was checked; actual recorded executions used local Python 3.12.14 and container Python 3.13.14, not every supported Python/OS combination.
- Tests and reviews reduce risk; they cannot prove the absence of every bug or guarantee recruiter scoring.

## 13. Scoring and recruitment context

Published rubric:

| Category | Points |
| --- | ---: |
| Usable result | 40 |
| Accuracy and verification | 25 |
| Prioritization | 20 |
| Communication and handoff | 15 |

A clear, tested core can earn full marks. Tool choice, AI-detector judgments, prose polish, hours worked and sheer output volume are not scored according to the README. Optional complexity does not automatically improve the score.

Earlier informal assessments included 84 and later approximately 95/100; these were estimates, not company grades. Do not present them as measured facts or promise 100. The final recommendation was to submit because no remaining blocking issue had been found in the checks performed.

The user found Ostorlab's public examples repository:

https://github.com/Ostorlab/interview-project-examples.git

Their shared hiring post said those exact exercises were retired practice material. They show the format and emphasis on checking AI output, not guaranteed future interview questions. The user's exact invitation and assigned exercise remain the authority for their application.

## 14. Original-file integrity references

These SHA-256 values were checked during the final review:

```text
README.md
b264abdd5079b4b74906113b688fde02024fec9a81a4772352d48e2428212cdb

inputs/primary.json
16bb9cff13c2294b7edba02a7301a4c2a98577de50d67da281382efd629b4f65

inputs/secondary.json
fc22f140c10cd456cf38b17c0ff15b91fb097e3a77316180f2c34189f2e64f26

inputs/malformed-input.txt
168e4d1efa2ff7a96d7cc21162069fe7fd445ec9ae7923c819050516b63bfc8c
```

Do not use this document as permission to change those files.

## 15. Local tools and audit artifacts, if continuing on the same PC

The agent environment used this interpreter because its shell did not expose `python` on PATH:

```text
C:\Users\HP\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
```

That is an agent-machine detail, not an application dependency. Other PCs should use their own Python 3.10+ interpreter.

Private audit artifacts were stored outside the project:

```text
C:\Users\HP\.codex\visualizations\2026\10\21\01a15e67-fde1-7520-b424-3325ffaa0502\final-project-review
```

They include native/container/archive audit scripts and reports. Some older reports/scripts refer to the previous embedded-video package and are historical. Do not run an older packaging script without inspecting it; it may re-add the video or expect the old file count. The actual final ZIP and the 20-file manifest above are the current packaging reference.

Video processing dependencies/models were temporary tools outside the application and were not bundled. An online speech service attempt was blocked before use; offline narration was used instead. Do not infer that project files were uploaded to that service.

## 16. Suggested first message to the next AI

> Read PROJECT_HANDOFF.md and inspect the attached final project ZIP before making claims about its current contents. The project is already prepared for submission. Do not modify the original README or supplied inputs, add test methods, re-add the video/SRT to the ZIP, or change documentation without a specific request. Explain things simply with small examples. My immediate question or requested next step is: [write it here].

End of handoff. Preserve the distinction between what was requested, what was implemented, what was actually tested, and what remains an assumption.
